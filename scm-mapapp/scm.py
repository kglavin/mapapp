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
        'status':'/api/scm.config/1.0.status',
        'sitelink':'api/scm.reporting/1.0/site/{id}'
    }

    which_item = choices.get(item, 'status')
    r = rq.get(realm + which_item.format(id=id), auth=(user,pw))    
    return r    
