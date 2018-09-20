from easysnmp import Session
import netrc 
import pprint

def get_num_interfaces(session):
	return session.get('IF-MIB::ifNumber.0').value

def get_if_ids(session):
        eths = []
        eths_name = []
        vtis = []
        vtis_name = []
        if_descs = session.bulkwalk('IF-MIB::ifDescr')
        for item in if_descs:
             if 'eth' in item.value:
                 eths.append(item.oid_index)
                 eths_name.append(item.value)
             if 'vti' in item.value:
                 if 'ip_vti0' not in item.value:
                     if 'ip6_vti0' not in item.value:
                        vtis.append(item.oid_index)
                        vtis_name.append(item.value)
        return (eths,eths_name,vtis, vtis_name)

def get_if_group(session, group, eth, vti):
    e = []
    v = [] 
    objs = session.bulkwalk(group,max_repetitions=20)
    for i in objs:
        if int(i.oid_index) in eth:
           e.append(i.value)
        if int(i.oid_index) in vti:
           v.append(i.value)
    return (e, v)


def poll_sites(sites, site_data, community):
    for k,v in sites.items():
           session = Session(hostname=v, community=community, version=2)
           data = {'id': k}	
           site_data[k] = data
           data['location'] = session.get('sysLocation.0').value
           data['numinterfaces'] = get_num_interfaces(session)
           data['eth_index'], data['eth_name'], data['vti_index'], data['vti_name'] =  get_if_ids(session)
           ethi = [int(n) for n in data['eth_index']]
           vtii = [int(n) for n in data['vti_index']]
           data['eth_status'],data['vti_status'] = get_if_group(session, 'IF-MIB::ifOperStatus', ethi, vtii)
           data['eth_ioctet'],data['vti_ioctet'] = get_if_group(session, 'IF-MIB::ifHCInOctets', ethi, vtii)
           data['eth_ooctet'],data['vti_ooctet'] = get_if_group(session, 'IF-MIB::ifHCOutOctets', ethi, vtii)
           data['eth_iunicast'],data['vti_iunicast'] = get_if_group(session, 'IF-MIB::ifHCInUcastPkts', ethi, vtii)
           data['eth_ounicast'],data['vti_ounicast'] = get_if_group(session, 'IF-MIB::ifHCOutUcastPkts', ethi, vtii)
    return




if __name__ == "__main__":
    import netrc 
    import time

    import pprint
    netrc = netrc.netrc()

    sites = { 
             'Dallas':'44.1.0.12',
             'Denver':'44.1.0.13',
             'Albuquerque':'44.1.0.14',
             'ElPaso':'44.1.0.15',
             'Houston':'44.1.0.16'
            }

    site_data = { }

    authTokens = netrc.authenticators('scm-snmp')
    community = authTokens[2]
    for t in range(10):
        poll_sites(sites,site_data,community)
        pprint.pprint(site_data)
        print("--",t,"--")
        time.sleep(30)

