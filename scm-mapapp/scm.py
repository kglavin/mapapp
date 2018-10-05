
#
# basic implmentation of the SteelConnect Rest API implemented 

# https://support.riverbed.com/apis/    using the 
# requests library and credentials that were retried from the netrc sub-system
# in this implementaition realm that be the full URL including the SCM org designation 
# or it can be just the realm portion, the results will be determinied by the RBAC 
# capabilities of the user credentials ( a realm admin account will return results for 
# for all orgs in that realm where as an org admin or read only will return just results 
# for that org even if a realm url is used without the org details)
#
import requests as rq


def get_status(realm, user, pw):
    r = rq.get( realm + '/api/scm.config/1.0/status', auth=(user,pw))
    return r

def get(item, realm, user,pw):
    choices = {
        'orgs':'/api/scm.config/1.0/orgs',
        'nodes':'/api/scm.config/1.0/nodes',
        'sites':'/api/scm.config/1.0/sites',
        'wans':'/api/scm.config/1.0/wans',
        'ports':'/api/scm.config/1.0/ports',
        'uplinks':'/api/scm.config/1.0/uplinks',
        'users':'/api/scm.config/1.0/users',
        'zones':'/api/scm.config/1.0/zones',
        'devices':'/api/scm.config/1.0/devices',
        'path_rules':'/api/scm.config/1.0/path_rules',
        'status':'/api/scm.config/1.0.status',
        'eventlogs':'/api/scm.reporting/1.0/event_logs',
        'uplinks_r':'/api/scm.reporting/1.0/uplinks',
    }
    which_item = choices.get(item, 'status')
    r = rq.get(realm + which_item, auth=(user,pw))    
    return r

def get_by_id(item, id, realm, user, pw):
    choices = {
        'org':'/api/scm.config/1.0/org/{id}',
        'node':'/api/scm.config/1.0/node/{id}',
        'site':'/api/scm.config/1.0/site/{id}',
        'wan':'/api/scm.config/1.0/wan/{id}',
        'port':'/api/scm.config/1.0/port/{id}',
        'uplink':'/api/scm.config/1.0/uplink/{id}',
        'user':'/api/scm.config/1.0/user/{id}',
        'zone':'/api/scm.config/1.0/zone/{id}',
        'device':'/api/scm.config/1.0/device/{id}',
        'path_rule':'/api/scm.config/1.0/path_rule/{id}',
        'status':'/api/scm.config/1.0/status',
        'sitelinks':'/api/scm.reporting/1.0/site/{id}/sitelinks',
    }

    which_item = choices.get(item, 'status')
    r = rq.get(realm + which_item.format(id=id), auth=(user,pw))    
    return r    
