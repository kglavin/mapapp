
import os
import datetime
import pandas as pd
import scm as scm
import gpslocation as gps
from math import sin, cos, atan2, sqrt, radians, degrees


gpsdict = gps.gendict()

sitedf = pd.DataFrame([],  columns =  ['site', 'lat', 'lon','leafs','region'])
nodedf = pd.DataFrame([],  columns =  ['site','serial','router_id','region'])
eventdf = pd.DataFrame([],  columns =  ['Time','utc', 'Message', 'Severity','region'])


def get_sites(sitedf, realm, user, pw, region=0):
    r = scm.get('sites', realm, user,pw)
    if r.status_code == 200:
        f = r.json()
        for a in f['items']:
            p = gpsdict[a['city']]
            lat = p['lat']
            lon = p['lon']
            sitedf.loc[a['id']] = [a['city'], lat, lon,a['sitelink_leafs'],region]
    return

def get_sites_dict(site_dict, realm, user, pw, region=0):
    r = scm.get('sites', realm, user,pw)
    if r.status_code == 200:
        f = r.json()
        for a in f['items']:
            p = gpsdict[a['city']]
            lat = p['lat']
            lon = p['lon']
            site_dict[a['id']] = { 'site':a['city'], 'lat':lat, 'lon':lon, 'leafs': a['sitelink_leafs'],'region':region}
    return

def get_nodes(nodedf, sitedf, realm, user, pw, region=0):
    r = scm.get('nodes', realm, user,pw)
    if r.status_code == 200:
        f = r.json()
        for a in f['items']:
            city = sitedf.loc[a['site']]['site']
            nodedf.loc[a['id']] = [city, a['serial'], a['router_id'],region] 
    return

def get_nodes_dict(node_dict, site_dict, realm, user, pw, regions=0):
    r = scm.get('nodes', realm, user,pw)
    if r.status_code == 200:
        f = r.json()
        for a in f['items']:
            city = site_dict[a['site']]['site']
            node_dict[a['id']] = { 'site':city, 'serial':a['serial'], 'router_id':a['router_id'],'region':region}
    return

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

def get_eventlogs_dict(event_dict,realm, user, pw, region=0):
    r = scm.get('eventlogs', realm, user,pw)
    if r.status_code == 200:
        f = r.json()
        for a in f['items']:
            event_dict[a['id']] = { 'time':datetime.datetime.fromtimestamp(a['utc']).strftime('%c'),
                                    'utc':a['utc'],
                                    'Message':a['msg'],
                                    'Severity':a['severity'],
                                    'region':region}
    return


def find_tunnel_relationships(sitedf,region=0):
    ll = []
    r = []
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


def scattermapbox_line(a_lat, a_lon, z_lat, z_lon):
    return { 
            'lat': [a_lat, z_lat ],
            'lon': [a_lon , z_lon ],
            'type': 'scattermapbox',
            'mode':'lines',
            'line':{ 'size':1, 'color': 'rgb(255, 0, 0)' },
            }

def generate_tunnels(sitedf, region=0):
    r = find_tunnel_relationships(sitedf,region)
    lines = []
    for e in r:
        ((a_name, a_lat, a_lon),(z_name, z_lat, z_lon)) = e 
        lines.append(scattermapbox_line(a_lat, a_lon, z_lat, z_lon))
    return lines

#    return [{                                                     
#            'lat': [52.37, 50.12 ],
#            'lon': [4.9 , 8.68 ],
#            'type': 'scattermapbox',
#            'mode':'lines',
#            'line':{ 'size':1, 'color': 'rgb(255, 0, 0)' },
#              },
#            {                                                     
#            'lat': [52.37, 48.85 ],
#            'lon': [4.9 , 2.35 ],
#            'type': 'scattermapbox',
#            'mode':'lines',
#            'line':{ 'size':1, 'color': 'rgb(255, 0, 0)' },
#            }]

def generate_sites(sitedf, region=0):
    '''region=0 is all sites'''
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
    if region == 0:
        lat = sitedf['lat']
        lon = sitedf['lon']
    else:
        lat = sitedf.loc[sitedf['region'] == region]['lat']
        lon = sitedf.loc[sitedf['region'] == region]['lon']

    print('lat=',lat)
    print('lon=',lon)
    x=0.0
    y=0.0
    z=0.0

    for s in lat.index:
        la = float(radians(lat.loc[s]))
        lo = float(radians(lon.loc[s]))
        x += cos(la) * cos(lo)
        y += cos(la) * sin(lo)
        z += sin(la)

    x = float(x / lat.count)
    y = float(y / lat.count)
    z = float(z / lat.count)
    #(lat, lon)
    return (degrees(atan2(z, sqrt(x * x + y * y))), degrees(atan2(y, x)))


    