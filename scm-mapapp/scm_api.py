
import os
import datetime
import pandas as pd
import scm as scm
import gpslocation as gps


gpsdict = gps.gendict()

def get_sites(sitedf, realm, user, pw):
    r = scm.get('sites', realm, user,pw)
    if r.status_code == 200:
        f = r.json()
        for a in f['items']:
            p = gpsdict[a['city']]
            lat = p['lat']
            lon = p['lon']
            sitedf.loc[a['id']] = [a['city'], lat, lon,a['sitelink_leafs']]
    return

def get_nodes(nodedf, sitedf, realm, user, pw):
    r = scm.get('nodes', realm, user,pw)
    if r.status_code == 200:
        f = r.json()
        for a in f['items']:
            city = sitedf.loc[a['site']]['site']
            nodedf.loc[a['id']] = [city, a['serial'], a['router_id']] 
    return

def get_eventlogs(eventdf,realm, user, pw):
    r = scm.get('eventlogs', realm, user,pw)
    if r.status_code == 200:
        f = r.json()
        for a in f['items']:
            eventdf.loc[a['id']] = [datetime.datetime.fromtimestamp(a['utc']).strftime('%c'),
                                    a['utc'],
                                    a['msg'],
                                    a['severity']]
    return

def generate_tunnels(sitedf):
    return {                                                     
            'lat': [52.37, 50.12 ],
            'lon': [4.9 , 8.68 ],
            'type': 'scattermapbox',
            'mode':'lines',
            'line':{ 'size':1, 'color': 'rgb(255, 0, 0)' },
    }

def generate_sites(sitedf):
    return {                                                     
            'lat': sitedf['lat'],
            'lon': sitedf['lon'],
            'type': 'scattermapbox',
            'mode':'markers',
            'marker':{ 'size':10, 'color': 'rgb(0, 225, 0)' },
            'text': sitedf['site']
    }
    