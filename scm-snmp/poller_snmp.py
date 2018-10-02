#
# routines to poll snmp information from the appliances 
# using the easysnmp library. 
# 
# bulk polled data is placed in a pivoted Pandas dataframe to allow it to be easily entered in a 
# time series database on a per site/interface basis. 

from easysnmp import Session
import netrc 
import pprint
from time import gmtime, strftime
import time
import multiprocessing as mp

def get_num_interfaces(session):
    ''' get the number of interfaces on the target device, 
      can be used a quick ping to see if the device is alive
      '''
    return session.get('IF-MIB::ifNumber.0').value

def get_if_ids(session):
    ''' parse out the interface description table and return a 
      valid list of ethernet and virtual tunnel names and indexs
      '''
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
              # no interested in the generic ip and ipv6 vti devices, just the 
              # specific provisioned tunnel interfaces
              if 'ip_vti0' not in item.value:
                  if 'ip6_vti0' not in item.value:
                      vtis.append(item.oid_index)
                      vtis_name.append(item.value)
    except:
      pass
    return (eths,eths_name,vtis, vtis_name)

def get_if_group(session, group, eth, vti):
    ''' for a specfic mib group, get the group and only return the 
        values associated with the provided ethernet and vti index numbers
        using bulkwalk to get the table in bulk should be more efficent in terms 
        of round trips then individually querying the interfaces 
        '''
    e = []
    v = [] 
    objs = []
    try:
      objs = session.bulkwalk(group,max_repetitions=20)
    except:
      pass
    for i in objs:
        if int(i.oid_index) in eth:
           e.append(i.value)
        if int(i.oid_index) in vti:
           v.append(i.value)
    return (e, v)


def poll_site(site, hostname, community='public'):
  ''' given a site tag and ip addresses/hosts, use the provided community string to 
  collect the values for the set of ethernet and virtual tunnel interfaces that are on the target device
  '''
  data = {'id': site}    
  data['time'] = time.strftime('%Y-%m-%dT%H:%M:%S', gmtime())
  session = Session(hostname=hostname, community=community, version=2) 

  try:    
      data['location'] = session.get('sysLocation.0').value
  except:
      print(e)
      data['Location'] = 'Dead'
      raise

  if data['Location'] is not 'Dead':
    try:
      data['numinterfaces'] = get_num_interfaces(session)
      data['eth_index'], data['eth_name'], data['vti_index'], data['vti_name'] =  get_if_ids(session)
      ethi = [int(n) for n in data['eth_index']]
      vtii = [int(n) for n in data['vti_index']]
    except Exception as e:
      print(e)
      data['eth_status'],data['vti_status'] = [],[]
      raise
    try:
        data['eth_status'],data['vti_status'] = get_if_group(session, 'IF-MIB::ifOperStatus', ethi, vtii)
    except Exception as e:
        print(e)
        data['eth_status'],data['vti_status'] = [],[]
        raise
    try:
        data['eth_ioctet'],data['vti_ioctet'] = get_if_group(session, 'IF-MIB::ifHCInOctets', ethi, vtii)
    except Exception as e:
        print(e)
        data['eth_ioctet'],data['vti_ioctet'] = [],[]
        raise
    try:
        data['eth_ooctet'],data['vti_ooctet'] = get_if_group(session, 'IF-MIB::ifHCOutOctets', ethi, vtii)
    except Exception as e:
        print(e)
        data['eth_ooctet'],data['vti_ooctet'] = [],[]
        raise
    try:
        data['eth_iunicast'],data['vti_iunicast'] = get_if_group(session, 'IF-MIB::ifHCInUcastPkts', ethi, vtii)
    except Exception as e:
        print(e)
        data['eth_iunicast'],data['vti_iunicast'] = [],[]
        raise
    try:
        data['eth_ounicast'],data['vti_ounicast'] = get_if_group(session, 'IF-MIB::ifHCOutUcastPkts', ethi, vtii)
    except Exception as e:
        print(e)
        data['eth_ounicast'],data['vti_ounicast'] = [],[]
        raise
  return data

def poll_sites(sites,community='public'):
  ''' given a dictionary of sites and the associated ip addresses, use the provided community string to 
  collect the values for the set of ethernet and virtual tunnel interfaces that are on the target device
  '''
  site_data = {}
  for k,v in sites.items():
      d = poll_site(k,v,community)
      site_data[k] = d
  return site_data


def mp_poll_sites(pool,sites,community='public'):
  ''' given a dictionary of sites { 'id': x, 'hostname': y} and the associated ip addresses, use the provided community string to 
  collect the values for the set of ethernet and virtual tunnel interfaces that are on the target device
  using the python multiprocessing subsystem to process a number of the snmp polls in parallel, this will 
  mask some of the roundtrip latency that accumumaltes if we query each appliance serially (as well as the serial queries to 
  multiple snmp groups being made that this implementation does not address) '''
  #pool = mp.Pool(processes=4)
  site_data = {}
  results = [pool.apply(poll_site, args=(k,v,community)) for k,v in sites.items()]
  for r in results:
    site_data[r['id']] = r
  return site_data


def pivot_sitedata(sd,if_type='eth'):
  ''' the sitedata for a specific site needs to be pivoted into a format that 
      allows the data to be inserted in the influxdb time series, 
      the input site data is structured where all measurements are bundled indexed by inteface index.
      for the time series we want a linear instance, with device name, and interface id along with all
      the associated measured values,   these measurements are returned as a list of measurement dictionaries
      '''
  ret = []
  if if_type not in ['eth','vti']:
      return ret
  if sd['location'] == 'Dead':
      return ret      
  es = sd[if_type+'_name'] 
  ind=0
  for e in es: 
      d = dict()           
      d['measurement'] = 'ifstats'
      d['tags'] = { 'site': sd['location'],
                    'id': sd['id'], 
                    'if_name': e  } 
      d['time'] =  sd['time']
      d['fields'] =  {  'in_octets'  : sd[if_type+'_ioctet'][ind],
                        'out_octets' : sd[if_type+'_ooctet'][ind],
                        'in_unicast' : sd[if_type+'_iunicast'][ind],
                        'out_unicast': sd[if_type+'_ounicast'][ind],
                        'status'     : sd[if_type+'_status'][ind]}
      ret.append(d)
      ind += 1
  return ret

