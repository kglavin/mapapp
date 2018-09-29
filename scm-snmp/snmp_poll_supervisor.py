#
# daemon that polls standard SNMP information from a set of provided 
# appliances/sites
# netrc is used to store the community string, currently the same string is 
# used for all instnaces 
#
# bulk received data is sent to the timeseries data to be stored. 
# currently period of SNMP queries is set to 15 seconds 
#
# This implementation uses a multi process implemntation so there are 
# multiple slave instances that undertake the snmp polling so that 
# this polling can be happening in parallel to a set of sites instead
# of sequentially polling each unique site/appliance
# the results of a single cycle of polling is sent as a batch to the 
# time series database by the master process, it is expected that the 
# polling nodes are close to the time series node so there is more latency 
# between polling and appliance versus master poll node and time series database, 
# so batch insert should be fast across a high speed low latency connection. 

from easysnmp import Session
import multiprocessing as mp
import netrc 
import time
from poller_snmp import mp_poll_sites, poll_sites, pivot_sitedata
from influxdb import InfluxDBClient
import pprint

if __name__ == "__main__":
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
    pool = mp.Pool(processes=4)

    while True:
        measurements = [ ]
        start_poll_time = time.time()
        site_data = mp_poll_sites(pool,sites,community)
        for k,v in site_data.items():
          for n in pivot_sitedata(v,'eth'):
             measurements.append(n)
          for n in pivot_sitedata(v,'vti'):
             measurements.append(n)
        try:
          client.write_points(measurements,time_precision='s')
        except:
            pass
        now_time = time.time()
        poll_time = now_time-start_poll_time
        if int(poll_time) < 15:
          time.sleep(15-int(poll_time))
        else:
          time.sleep(5)

