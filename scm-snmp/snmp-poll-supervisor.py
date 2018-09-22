from easysnmp import Session
import netrc 
import pprint
import time
from poller-snmp import poll_sites, pivot_sitedata
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

    while True:
        measurements = [ ]
        start_poll_time = time.time()
        site_data = poll_sites(sites,community)
        for k,v in site_data.items():
          measurements.append(pivot_sitedata('eth',v))
          measurements.append(pivot_sitedata('vti',v))
        try:
          client.write_points(measurements,time_precision='ms')
        except:
            pass
        now_time = time.time()
        poll_time = now_time-start_poll_time
        if int(poll_time) < 30:
          time.sleep(30-int(poll_time)
        else:
          time.sleep(20)

