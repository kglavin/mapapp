#
# a daemon that periocially polls the SCM realms via rest api, 
# this data is then stored in the proxy cache for use by other 
# subsytems
# 
# currently hard coded to poll every 10 minutes.  
#
import multiprocessing as mp
import netrc 
import time
import requests as rq
from scm_api import init_sitedf, sitedf, init_nodedf, nodedf, init_eventdf, eventdf,uplinkdf, init_uplinkdf, init_sites_snmp, sites_snmpdf, get_sites, get_nodes, get_eventlogs, get_uplinks, gen_sites_snmp, post_sites_snmp


if __name__ == "__main__":
    netrc = netrc.netrc()
    realm = 'https://catfish3.riverbed.cc'
    hosts = ['kglavin-us', 'kglavin-eur', 'kglavin-asia' ]
    users = []
    pw=[]
    regions = []

    proxy = "http://127.0.0.1:8040"

#    pool = mp.Pool(processes=4)

    while True:
        globals()['sitedf']       = init_sitedf()
        globals()['nodedf']       = init_nodedf()
        globals()['eventdf']      = init_eventdf()
        globals()['sites_snmpdf'] = init_sites_snmp()
        globals()['uplinkdf']     = init_uplinkdf()

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
            get_uplinks(uplinkdf, sitedf, realm, user, pw, region)
            get_eventlogs(eventdf,realm,user,pw,region)
            region += 1

        gen_sites_snmp(sites_snmpdf,uplinkdf) 
        post_sites_snmp(proxy, sites_snmpdf)

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
