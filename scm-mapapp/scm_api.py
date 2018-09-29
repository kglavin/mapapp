
import os
import datetime
import pandas as pd
import requests as rq
import scm as scm
import gpslocation as gps
from math import sin, cos, atan2, sqrt, radians, degrees


gpsdict = gps.gendict()

def init_sitedf():
    return pd.DataFrame([],  columns =  ['site', 'lat', 'lon','leafs','region', 'fm_state'])
def init_sites_snmp():
    return pd.DataFrame([],  columns =  ['site', 'v4ip', 'wan'])
def init_nodedf():
    return pd.DataFrame([],  columns =  ['site','serial','router_id','region'])
def init_uplinkdf():
    return pd.DataFrame([],  columns =  ['site', 'v4ip', 'wan'])
def init_eventdf():
    return pd.DataFrame([],  columns =  ['Time','utc', 'Message', 'Severity','region'])

sitedf       = init_sitedf()
sites_snmpdf = init_sites_snmp()
nodedf       = init_nodedf()
uplinkdf     = init_uplinkdf()
eventdf      = init_eventdf()

def get_sites(sitedf, realm, user, pw, region=0):
    r = scm.get('sites', realm, user,pw)
    if r.status_code == 200:
        f = r.json()
        for a in f['items']:
            p = gpsdict[a['city']]
            lat = p['lat']
            lon = p['lon']
            sitedf.loc[a['id']] = [a['city'].replace(" ","_"), lat, lon,a['sitelink_leafs'],region,0]
    return

def get_sites_proxy(proxy,user="",pw=""):
    r = rq.get(proxy + '/api/sites', auth=(user,pw))
    if r.status_code == 200:
        df =  pd.read_json(r.content, orient='index')
        return df
    else:
        return init_sitesdf()


def get_nodes(nodedf, sitedf, realm, user, pw, region=0):
    r = scm.get('nodes', realm, user,pw)
    if r.status_code == 200:
        f = r.json()
        for a in f['items']:
            city = sitedf.loc[a['site']]['site']
            nodedf.loc[a['id']] = [city, a['serial'], a['router_id'],region] 
    return

def get_nodes_proxy(proxy,user="",pw=""):
    r = rq.get( proxy + '/api/nodes', auth=(user,pw))
    if r.status_code == 200:
        return pd.read_json(r.content, orient='index')
    else:
        return init_nodesdf()


def get_eventlogs(eventdf,realm, user, pw, region=0):
    r = scm.get('eventlogs', realm, user,pw)
    if r.status_code == 200:
        f = r.json()
        for a in f['items']:
            eventdf.loc[a['id']] = [datetime.datetime.fromtimestamp(a['utc']).strftime('%c'),
                                    a['utc'],
                                    a['msg'],
                                    a['severity'],
                                    region]
    return


def get_eventlogs_proxy(proxy, user="",pw=""):
    r = rq.get( proxy + '/api/eventlogs', auth=(user,pw))
    if r.status_code == 200:
        return pd.read_json(r.content, orient='index')
    else:
        return init_eventdf()


def get_uplinks(uplinkdf, sitedf, realm, user, pw, region=0):
    r = scm.get('uplinks_r', realm, user,pw)
    if r.status_code == 200:
        f = r.json()
        for a in f['items']:
            #print(a['id'], a['site'], a['v4ip'])
            city = sitedf.loc[a['site']]['site']
            uplinkdf.loc[a['id']] = [city, a['v4ip'], a['wan']] 
    return

def get_uplinks_proxy(proxy,user="",pw=""):
    r = rq.get( proxy + '/api/uplinks', auth=(user,pw))
    if r.status_code == 200:
        return pd.read_json(r.content, orient='index')
    else:
        return init_uplinksdf()


def gen_sites_snmp(sites_snmpdf,uplinkdf):
    a = uplinkdf[uplinkdf['wan'].str.contains('wan-Internet')].dropna()
    for i, row in a.iterrows():
        print(row)
        sites_snmpdf.loc[i] = row
    return 

def post_sites_snmp(proxy, sites_snmpdf):
    r = rq.post(proxy+'/api/sites/snmp_details', json=sites_snmpdf.to_json(orient='index'))
    return

def get_sites_proxy(proxy,user="",pw=""):
    r = rq.get( proxy + '/api/sites/snmp_details', auth=(user,pw))
    if r.status_code == 200:
        return pd.read_json(r.content, orient='index')
    else:
        return init_sites_snmpdf()

def find_tunnel_relationships(sitedf,region=0):
    ll = []
    r = []
    if len(sitedf) < 1:
        return r
    for s in sitedf.index:
        if region == 0:
            if len(sitedf.loc[s]['leafs']) > 0 :
                ll.append((s,sitedf.loc[s]['leafs']))
        else:
         if sitedf.loc[s]['region'] == region :
            if len(sitedf.loc[s]['leafs']) > 0 : 
                ll.append((s,sitedf.loc[s]['leafs']))
    for a in ll:
        (h,sl) = a
        h_city = sitedf.loc[h]['site']
        for s in sl:
            s_city =sitedf.loc[s]['site']
            r.append(((h_city,sitedf.loc[h]['lat'],sitedf.loc[h]['lon']),
                      (s_city,sitedf.loc[s]['lat'],sitedf.loc[s]['lon'])))
    return r


def scattermapbox_line(a_lat, a_lon, z_lat, z_lon, color='rgb(255, 0, 0)'):
    return { 
            'lat': [a_lat, z_lat ],
            'lon': [a_lon , z_lon ],
            'type': 'scattermapbox',
            'mode':'lines',
            'line':{ 'size':1, 'color': color },
            }

def generate_tunnels(sitedf, region=0):
    lines = []
    if len(sitedf) < 1:
        return lines
    r = find_tunnel_relationships(sitedf,region)
    for e in r:
        ((a_name, a_lat, a_lon),(z_name, z_lat, z_lon)) = e 
        lines.append(scattermapbox_line(a_lat, a_lon, z_lat, z_lon))
    return lines

def generate_sites(sitedf, region=0):
    '''region=0 is all sites'''
    if len(sitedf)<1:
        return {}
    if region == 0:
        l = {                                                     
            'lat': sitedf['lat'],
            'lon': sitedf['lon'],
            'type': 'scattermapbox',
            'mode':'markers',
            'marker':{ 'size':10, 'color': 'rgb(0, 225, 0)' },
            'text': sitedf['site']
        }
    else:
        l = {                                                     
            'lat': sitedf.loc[sitedf['region'] == region]['lat'],
            'lon': sitedf.loc[sitedf['region'] == region]['lon'],
            'type': 'scattermapbox',
            'mode':'markers',
            'marker':{ 'size':10, 'color': 'rgb(0, 225, 0)' },
            'text': sitedf['site']
        }
    return l

def latlon_midpoint(sitedf, region=0):
    ''' see http://www.geomidpoint.com/calculation.html'''
    if len(sitedf) < 1:
        return(0,-180)
    if region == 0:
        lat = sitedf['lat']
        lon = sitedf['lon']
    else:
        lat = sitedf.loc[sitedf['region'] == region]['lat']
        lon = sitedf.loc[sitedf['region'] == region]['lon']

    x=0.0
    y=0.0
    z=0.0

    c = 0.0
    for s in lat.index:
        la = float(radians(lat.loc[s]))
        lo = float(radians(lon.loc[s]))
        x += cos(la) * cos(lo)
        y += cos(la) * sin(lo)
        z += sin(la)
        c += 1

    x = float(x / c)
    y = float(y / c)
    z = float(z / c)
    #(lat, lon)
    return (degrees(atan2(z, sqrt(x * x + y * y))), degrees(atan2(y, x)))


    
