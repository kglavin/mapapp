#
# unility libraary that provides capabilies to interact with the SCM instances and provide 
# the retrieved data in a format for presentation. 
#
# this library provides functions for communicating directly with an SCM instnace 
# and it also provides functions with the _proxy naming where the data is retrived 
# from the proxy cache function instance of going directly to the SCM. 
# this is the help with scalability of the implmentation where the number of transactions 
# against the SCM rest interfaces are limited and it also provdes for a more responsive 
# rendering of the application pages ( at the expense of data age.)
#
import os
import datetime
import pandas as pd
import requests as rq
import scm as scm
import gpslocation as gps
from math import sin, cos, atan2, sqrt, radians, degrees
import json


gpsdict = gps.gendict()


# 
# Pandas dataframe are used in a global fashion to hold the data that is receoved form the SCM instances. 
def init_sitedf():
    return pd.DataFrame([],  columns =  ['site', 'lat', 'lon','leafs','region', 'fm_state'])
def init_sites_snmp():
    return pd.DataFrame([],  columns =  ['site', 'v4ip', 'wan'])
def init_nodedf():
    return pd.DataFrame([],  columns =  ['site','serial','router_id','region'])
def init_uplinkdf():
    return pd.DataFrame([],  columns =  ['site', 'v4ip', 'wan','region'])
def init_eventdf():
    return pd.DataFrame([],  columns =  ['Time','utc', 'Message', 'Severity','region'])

sitedf       = init_sitedf()
sites_snmpdf = init_sites_snmp()
nodedf       = init_nodedf()
uplinkdf     = init_uplinkdf()
eventdf      = init_eventdf()


def get_sites(sitedf, realm, user, pw, region=0):
    ''' populate the provided pandas dataframe with the site information, 
        as this data is entered into the dataframe each row is annotated with the region that 
        the site is assocated with 
        '''
    r = scm.get('sites', realm, user,pw)
    if r.status_code == 200:
        f = r.json()
        for a in f['items']:
            try:
                p = gpsdict[a['city']]
            except:
                #unknown cites will be stacked at (0,0) on the map as the gps data is not extensive
                p = { 'lat':0, 'lon':0}
            lat = p['lat']
            lon = p['lon']
            sitedf.loc[a['id']] = [a['city'].replace(" ","_"), lat, lon,a['sitelink_leafs'],region,{'size':10, 'symbol':'triangle', 'color': 'rgb(0, 255, 0)'}]
    return

def get_sites_proxy(df, proxy,user="",pw=""):
    ''' get the sites data using the proxy instead of directly 
        returns a pandas data frame with the received data or empty on a problem
        '''
    r = rq.get(proxy + '/api/sites', auth=(user,pw))
    if r.status_code == 200:
        df.append(pd.read_json(r.content, orient='index'))
        return df
    else:
        return df.append(init_sitesdf())


def get_nodes(nodedf, sitedf, realm, user, pw, region=0):
    ''' populate the provided pandas dataframe with the node information, 
        as this data is entered into the dataframe each row is annotated with the region that 
        the node is assocated with, defaults to 0 region
        '''
    r = scm.get('nodes', realm, user,pw)
    if r.status_code == 200:
        f = r.json()
        for a in f['items']:
            city = sitedf.loc[a['site']]['site']
            nodedf.loc[a['id']] = [city, a['serial'], a['router_id'],region] 
    return

def get_nodes_proxy(proxy,user="",pw=""):
    ''' get the nodes data using the proxy instead of directly 
        returns a pandas data frame with the received data or empty on a problem
        '''
    r = rq.get( proxy + '/api/nodes', auth=(user,pw))
    if r.status_code == 200:
        return pd.read_json(r.content, orient='index')
    else:
        return init_nodesdf()


def get_eventlogs(eventdf,realm, user, pw, region=0):
    ''' populate the provided pandas dataframe with the eventlog information, 
        as this data is entered into the dataframe each row is annotated with the region that 
        the node is assocated with, defaults to 0 region
        '''
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
    ''' get the eventlog data using the proxy instead of directly 
        returns a pandas data frame with the received data or empty on a problem
        '''
    r = rq.get( proxy + '/api/eventlogs', auth=(user,pw))
    if r.status_code == 200:
        return pd.read_json(r.content, orient='index')
    else:
        return init_eventdf()


def get_uplinks(uplinkdf, sitedf, realm, user, pw, region=0):
    ''' populate the provided pandas dataframe with the uplink information, 
        as this data is entered into the dataframe each row is annotated with the region that 
        the node is assocated with, defaults to 0 region
        '''
    r = scm.get('uplinks_r', realm, user,pw)
    if r.status_code == 200:
        f = r.json()
        for a in f['items']:
            city = sitedf.loc[a['site']]['site']
            uplinkdf.loc[a['id']] = [city, a['v4ip'], a['wan'],region] 
    return

def get_uplinks_proxy(proxy,user="",pw=""):
    ''' get the uplinks data using the proxy instead of directly 
        returns a pandas data frame with the received data or empty on a problem
        '''
    r = rq.get( proxy + '/api/uplinks', auth=(user,pw))
    if r.status_code == 200:
        return pd.read_json(r.content, orient='index')
    else:
        return init_uplinksdf()


def gen_sites_snmp(sites_snmpdf,uplinkdf):
    ''' using the uplinks data, massage and filter it to provide a 
        frame of the site/appliance name/ip that should be polled. 
        currently this information is just getting an ipv4 address off the 
        internet uplink -- which may not be the correct/desired action in a real 
        deployment
        '''
    a = uplinkdf[uplinkdf['wan'].str.contains('wan-Internet')].dropna()
    for i, row in a.iterrows():
        sites_snmpdf.loc[i] = row
    return 

def post_sites_snmp(proxy, sites_snmpdf):
    ''' post the snmp site detail information onto the proxy cache'''
    r = rq.post(proxy+'/api/snmp_details', json=sites_snmpdf.to_json(orient='index'))
    return

def get_sites_snmp_proxy(proxy,user="",pw=""):
    ''' get the snmp site information from the proxy cache'''
    r = rq.get( proxy + '/api/snmp_details', auth=(user,pw))
    if r.status_code == 200:
        return pd.read_json(r.content, orient='index')
    else:
        return init_sites_snmpdf()

def get_sites_state_proxy(proxy,user="",pw=""):
    ''' get the snmp site state information (if.location) from the proxy cache'''
    r = rq.get(proxy + '/api/sites_state', auth=(user,pw))
    if r.status_code == 200:
        return json.loads(r.content)
    else:
        return {}

def find_tunnel_relationships(sitedf,region=0):
    ''' using the site data frame, derive the tunnel relationships 
        currently this implementation just derives the hub and spoke relationships 
        and provides a list of tuples that indicate spoke to hub connections. 
        this implementation does not handle dual-hub ( bug in SCM rest api) and 
        it does not enumerate the full mesh link members
        '''
    ll = []
    r = []
    if len(sitedf) < 1:
        return r

    # for all the site entries find elements that have reference entried in their leaf attribute
    # add them the ll list
    for s in sitedf.index:
        if region == 0:
            if len(sitedf.loc[s]['leafs']) > 0 :
                ll.append((s,sitedf.loc[s]['leafs']))
        else:
         if sitedf.loc[s]['region'] == region :
            if len(sitedf.loc[s]['leafs']) > 0 : 
                ll.append((s,sitedf.loc[s]['leafs']))
    # for each of the entries on this list, 
    # derive the site/city information and also get the 
    # lat/lon entries for both ends of the link 
    # add these to the return list r
    for a in ll:
        (h,sl) = a
        h_city = sitedf.loc[h]['site']
        for s in sl:
            s_city =sitedf.loc[s]['site']
            r.append(((h_city,sitedf.loc[h]['lat'],sitedf.loc[h]['lon']),
                      (s_city,sitedf.loc[s]['lat'],sitedf.loc[s]['lon'])))
    return r



def scattermapbox_line(a_lat, a_lon, z_lat, z_lon, color='rgb(255, 0, 0)'):
    ''' create a mapbox line definition using a and z lat/lon and also a color'''
    return { 
            'lat': [a_lat, z_lat ],
            'lon': [a_lon , z_lon ],
            'type': 'scattermapbox',
            'mode':'lines',
            'line':{ 'size':1, 'color': color },
            }


def generate_tunnels(sitedf, region=0):
    ''' for the sites dataframe, figure out all the tunnels for the provided region, 
        region == 0 means everything and return a list of mapbox line defintions to 
        be rendered on the map
        '''
    lines = []
    if len(sitedf) < 1:
        return lines
    r = find_tunnel_relationships(sitedf,region)
    for e in r:
        ((a_name, a_lat, a_lon),(z_name, z_lat, z_lon)) = e 
        lines.append(scattermapbox_line(a_lat, a_lon, z_lat, z_lon))
    return lines

def generate_sites(sitedf, region=0):
    '''region=0 is all sites, create the mapbox marker defintions for the sites'''
    if len(sitedf)<1:
        return {}
    if region == 0:
        l = {                                                     
            'lat': sitedf['lat'],
            'lon': sitedf['lon'],
            'type': 'scattermapbox',
            'mode':'markers',
            'marker': sitedf['fm_state'],
            'text': sitedf['site']
        }
    else:
        l = {                                                     
            'lat': sitedf.loc[sitedf['region'] == region]['lat'],
            'lon': sitedf.loc[sitedf['region'] == region]['lon'],
            'type': 'scattermapbox',
            'mode':'markers',
            'marker': sitedf.loc[sitedf['region'] == region]['fm_state'],
            'text': sitedf['site']
        }
    return l

def latlon_midpoint(sitedf, region=0):
    ''' see http://www.geomidpoint.com/calculation.html, 
        figure out the gepgraphical center of gravity for the sites in the desired region
        (region == 0 means all sites) and return this lat/lon cordinate so it may be used
        to center the map'''
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


    
