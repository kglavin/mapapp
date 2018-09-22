from easysnmp import Session
import netrc 
import pprint
from time import gmtime, strftime

def get_num_interfaces(session):
	return session.get('IF-MIB::ifNumber.0').value

def get_if_ids(session):
        eths = []
        eths_name = []
        vtis = []
        vtis_name = []
        try:
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
        except:
          pass
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
        try :
          session = Session(hostname=v, community=community, version=2)
          data = {'id': k}	
          site_data[k] = data
          data['time'] = time.strftime('%Y-%m-%dT%H:%M:%S', gmtime())
          data['location'] = session.get('sysLocation.0').value
          data['numinterfaces'] = get_num_interfaces(session)
          data['eth_index'], data['eth_name'], data['vti_index'], data['vti_name'] =  get_if_ids(session)
          ethi = [int(n) for n in data['eth_index']]
          vtii = [int(n) for n in data['vti_index']]
          try:
            data['eth_status'],data['vti_status'] = get_if_group(session, 'IF-MIB::ifOperStatus', ethi, vtii)
          except:
            data['eth_status'],data['vti_status'] = [],[]
          try:
           data['eth_ioctet'],data['vti_ioctet'] = get_if_group(session, 'IF-MIB::ifHCInOctets', ethi, vtii)
          except:
            data['eth_ioctet'],data['vti_ioctet'] = [],[]
          try:
           data['eth_ooctet'],data['vti_ooctet'] = get_if_group(session, 'IF-MIB::ifHCOutOctets', ethi, vtii)
          except:
            data['eth_ooctet'],data['vti_ooctet'] = []. []
          try:
           data['eth_iunicast'],data['vti_iunicast'] = get_if_group(session, 'IF-MIB::ifHCInUcastPkts', ethi, vtii)
          except:
            data['eth_iunicast'],data['vti_iunicast'] = [], []
          try:
           data['eth_ounicast'],data['vti_ounicast'] = get_if_group(session, 'IF-MIB::ifHCOutUcastPkts', ethi, vtii)
          except:
            data['eth_ounicast'],data['vti_ounicast'] = [],[]
        except:
          pass
    return




if __name__ == "__main__":
    import netrc 
    import time
    from time import gmtime, strftime
    from influxdb import InfluxDBClient
    import json

    import pprint
    netrc = netrc.netrc()

    sites = { 
             'Memphis':'44.1.0.10',
             'Kansas':'44.1.0.11',
             'Dallas':'44.1.0.12',
             'Denver':'44.1.0.13',
             'Albuquerque':'44.1.0.14',
             'ElPaso':'44.1.0.15',
             'Houston':'44.1.0.16',
             'NewOrleans':'44.1.0.17',
             'SanAntonio':'44.1.0.18',
             'Amsterdam':'44.1.0.21',
             'Frankfurt':'44.1.0.23',
             'Paris':'44.1.0.22',
             'Bangkok':'44.1.0.31',
             'HochiMihn':'44.1.0.33',
             'KualaLumpar':'44.1.0.32',

            }

    authTokens = netrc.authenticators('scm-snmp')
    community = authTokens[2]
    client = InfluxDBClient(host='influxdb', port=8086)
    client.switch_database('scmdata')

    while True:
        site_data = { }
        json_body = [ ]
        start_poll_time = time.time()
        poll_sites(sites,site_data,community)
        for k,v in site_data.items():
          sd = v
          eths = sd['eth_name'] 
          ind=0
          for eth in eths:
            d = dict()
            d['measurement'] = 'ifstats'
            d['tags'] = { 'site': sd['location'],
                          'id': sd['id'], 
                          'if_name': eth  } 
            d['time'] =  sd['time']
            d['fields'] =  {  'in_octets': sd['eth_ioctet'][ind],
                              'out_octets': sd['eth_ooctet'][ind],
                              'in_unicast':sd['eth_iunicast'][ind],
                              'out_unicast':sd['eth_ounicast'][ind],
                              'status':sd['eth_status'][ind]} 
            json_body.append(d)
            ind += 1
          vtis = sd['vti_name'] 
          ind=0
          for vti in vtis:
            d = dict()
            d['measurement'] = 'ifstats'
            d['tags'] = { 'site': sd['location'],
                          'id': sd['id'], 
                          'if_name': vti  } 
            d['time'] =  sd['time']

            d['fields'] =  { 'in_octets': sd['vti_ioctet'][ind],
                             'out_octets': sd['vti_ooctet'][ind],
                             'in_unicast':sd['vti_iunicast'][ind],
                             'out_unicast':sd['vti_ounicast'][ind],
                             'status':sd['vti_status'][ind]} 
            json_body.append(d)
            ind += 1
        try:
          client.write_points(json_body,time_precision='ms')
        except:
            pass
        now_time = time.time()
        poll_time = now_time-start_poll_time
        if int(poll_time) < 30:
          time.sleep(30-int(poll_time)
        else:
          time.sleep(20)

