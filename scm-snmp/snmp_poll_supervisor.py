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

import os
from easysnmp import Session
import pandas as pd
import requests as rq
import multiprocessing as mp
import netrc 
import time
from poller_snmp import mp_poll_sites, poll_sites, pivot_sitedata
from influxdb import InfluxDBClient
import logging
import json

def update_sites_dict(proxy='http://127.0.0.1:8040'):
    ret = {}
    r = rq.get( proxy + '/api/snmp_details', auth=("",""))
    if r.status_code == 200:
        df =  pd.read_json(r.content, orient='index')
        for i in df.index:
            ret[df.loc[i]['site']] =  df.loc[i]['v4ip']
    return ret

def write_sites_status(site_status_list, proxy='http://127.0.0.1:8040'):
    r = rq.post(proxy+'/api/sites_state', json=json.dumps(site_status_list))
    return r

if __name__ == "__main__":
    netrc = netrc.netrc()
    logger = logging.getLogger('scm-snmp-poll')
    logger.setLevel(logging.DEBUG)
    logfilename = 'scm-snmp-poll.'+str(os.getpid())+'.log'
    fh = logging.FileHandler(logfilename)
    fh.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    logger.addHandler(fh)

    # initial site list, will be overwritten by dynamic list one its been calulated from SCM instances.
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

    measurement_count = 0
    good_measurement_writes = 0
    bad_measurement_writes = 0
    poll_time_measures = []

    sites_refresh_count = 20
    old_sites = {}

    logging.debug('starting main loop')
    while True:
        sites_refresh_count += 1
        if sites_refresh_count > 20: 
            sites_refresh_count = 0
            logging.info(f'''measurements: good writes - {good_measurement_writes}, bad writes - {bad_measurement_writes}, total metrics: {measurement_count}''')
            measurement_count = 0
            good_measurement_writes = 0
            bad_measurement_writes = 0
            poll_time_measures = []
            new_sites = update_sites_dict()
            if len(new_sites) > 0:
                old_sites = sites
                sites = new_sites
            else:
                #continue with existing sites 
                #but if sites is also empty try old sites
                logging.debug('new_sites return empty')
                if len(sites) < 1:
                    sites = old_sites
                    logging.debug('reverting to using old_sites')

        start_poll_time = time.time()
        if len(sites) > 0:            
            measurements = []
            status = []      
            site_data = mp_poll_sites(pool,sites,community)
            for k,v in site_data.items():
              # collect the location string as a proxy for an alive appliance. 
              status_d = dict()
              status_d['site'] =  v['location']
              status_d['id']   =  v['id']
              status_d['time'] =  v['time']
              status.append(status_d)

              # take the collected snmp data and pivot so its ready for inclusion into timeseries db. 
              for n in pivot_sitedata(v,'eth'):
                 measurements.append(n)
                 measurement_count +=1
              for n in pivot_sitedata(v,'vti'):
                 measurements.append(n)
                 measurement_count +=1
            try:
              client.write_points(measurements,time_precision='s')
              good_measurement_writes +=1
            except:
                bad_measurement_writes +=1
                logging.debug('failed to write_points')
                pass
            # send the status list to the api server so it can be used for realtime status of the nodes. 
            # can add link status later on. 
            #TODO
            try:
                write_sites_status(status)
            except:
                logging.debug('failed to write_sites_status')
                pass
        now_time = time.time()
        poll_time = now_time-start_poll_time
        if int(poll_time) < 15:
            poll_time_measures.append(poll_time)
            if sites_refresh_count == 20:
                logging.info('poll_times:'.join(str(e) for e in poll_time_measures))
                poll_time_measures = []
            time.sleep(15-int(poll_time))
        else:
            logging.debug('poll took longer that 15, throttling by 5')
            logging.info('poll_times:'.join(str(e) for e in poll_time_measures))
            poll_time_measures = []
            time.sleep(5)

