
import multiprocessing as mp
import netrc 
import time
import requests as rq
from scm_api import init_sitedf, sitedf, init_nodedf, nodedf, init_eventdf, eventdf, get_sites, get_nodes, get_eventlogs


if __name__ == "__main__":
    netrc = netrc.netrc()
    realm = 'https://catfish3.riverbed.cc'
    hosts = ['kglavin-us', 'kglavin-eur', 'kglavin-asia' ]
    users = []
    pw=[]
    regions = []

    proxy = "http://127.0.0.1:8040"

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

#    pool = mp.Pool(processes=4)

    while True:
        globals()['sitedf'] = init_sitedf()
        globals()['nodedf'] = init_nodedf()
        globals()['eventdf'] = init_eventdf()
        start_poll_time = time.time()
        region = 1
        for host in hosts:
            authTokens = netrc.authenticators(host)
            user = authTokens[0]
            users.append(user)
            pw = authTokens[2]
            regions.append(region)

            #TODO Change to Multiprocessing version later
            get_sites(sitedf, realm, user, pw, region)
            get_nodes(nodedf, sitedf, realm, user, pw,region)
            get_eventlogs(eventdf,realm,user,pw,region) 
            region += 1
        try:
            r = rq.post(proxy+'/api/sites', json=sitedf.to_json(orient='index'))
            r = rq.post(proxy+'/api/nodes', json=nodedf.to_json(orient='index'))
            r = rq.post(proxy+'/api/eventlogs', json=eventdf.to_json(orient='index'))
        except:
            pass
        now_time = time.time()
        poll_time = now_time-start_poll_time
        if int(poll_time) < 600:
          time.sleep(600-int(poll_time))
        else:
          time.sleep(300)
