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
    }

    which_item = choices.get(item, 'status')
    r = rq.get(realm + which_item, auth=(user,pw))    
    return r

def get_by_id(item, id, realm, user, pw):
    choices = {
        'org':'/api/scm.config/1.0/org/',
        'node':'/api/scm.config/1.0/node/',
        'site':'/api/scm.config/1.0/site/',
        'wan':'/api/scm.config/1.0/wan/',
        'port':'/api/scm.config/1.0/port/',
        'uplink':'/api/scm.config/1.0/uplink/',
        'user':'/api/scm.config/1.0/user',
        'zone':'/api/scm.config/1.0/zone',
        'device':'/api/scm.config/1.0/device',
        'path_rule':'/api/scm.config/1.0/path_rule',
        'status':'/api/scm.config/1.0.status'
    }

    which_item = choices.get(item, 'status')
    r = rq.get(realm + which_item + id, auth=(user,pw))    
    return r    
