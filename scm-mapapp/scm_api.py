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
def init_sitelinksdf():
    return pd.DataFrame([],  columns =  ['localcity','remotecity', 'local_site','local_node_serial', 'remote_node_serial','status', 'state','region'])

sitedf       = init_sitedf()
sites_snmpdf = init_sites_snmp()
nodedf       = init_nodedf()
uplinkdf     = init_uplinkdf()
eventdf      = init_eventdf()
sitelinksdf   = init_sitelinksdf()


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
            sitedf.loc[a['id']] = [a['city'].replace(" ","_"), lat, lon,a['sitelink_leafs'],region,{'size':10,'color': 'rgb(255, 0, 0)'}]
    return

def get_sites_proxy(proxy,user="",pw=""):
    ''' get the sites data using the proxy instead of directly 
        returns a pandas data frame with the received data or empty on a problem
        '''
    df = init_sitedf()
    r = rq.get(proxy + '/api/sites', auth=(user,pw))
    if r.status_code == 200:
        df = pd.read_json(r.content, orient='index')
        return df
    else:
        return df


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

#
# Sitelinks to derive tunnel relationships
#
def get_sitelinks(sitelinksdf, sitedf, realm, user, pw, region=0):
    ''' populate the provided pandas dataframe with the sitelink information, 
        as this data is entered into the dataframe each row is annotated with the region that 
        the node is assocated with, defaults to 0 region
        '''
    for s in sitedf.index:
        if sitedf.loc[s]['region'] == region or region == 0:
            sitename = sitedf.loc[s]['site']
            r = scm.get_by_id('sitelinks', s, realm, user,pw)
            if r.status_code == 200:
                f = r.json()
                for a in f['items']:
              #  "remote_node_serial":"XN45B3EA7F5AF641"
              #  "remote_site":"site-StLouis-a84ad2628cfb2b06"
              #  "local_site":"site-HQ-9759dcfb53b4a9d1"
              #  "local_node_serial":"XN8E48E858DD3F7C"
              #  "id":"XN45B3EA7F5AF641_vti4_1_1"
              # "status":"established"
              #  "state":"up"
                    localcity = sitedf.loc[a['local_site']]['site']
                    remotecity = sitedf.loc[a['remote_site']]['site']

                    sitelinksdf.loc[a['id']] = [localcity, 
                                                remotecity,
                                                a['local_site'],
                                                a['local_node_serial'],
                                                a['remote_node_serial'],
                                                a['status'],
                                                a['state'],
                                                region] 
    return

def post_sitelinks(proxy, sitelinksdf):
    ''' post the snmp sitelink detail information onto the proxy cache, this sitelink data provides a 
        list of the VTI interfaces and their connectivity to other sites 
    '''
    r = rq.post(proxy+'/api/sitelinks', json=sitelinksdf.to_json(orient='index'))
    return

def get_sitelinks_proxy(proxy,user="",pw=""):
    ''' get the snmp sitelink information from the proxy cache'''
    r = rq.get( proxy + '/api/sitelinks', auth=(user,pw))
    if r.status_code == 200:
        return pd.read_json(r.content, orient='index')
    else:
        return init_sitelinksdf()


#
# sitelinks processing 
#        
def build_vti_info(sitedf, region=0):
    vti_dict = {}
    sitelinksdf = get_sitelinks_proxy()
    for s in sitedf.index:
        if sitedf.loc[s]['region'] == region or region == 0:
            sitename = sitedf.loc[s]['site']
            vti_list = []
            for sl in sitelinksdf.index:
                if sitelinksdf.loc[sl]['localcity'] == sitename:
                    vti_list.append(sitelinksdf.loc[sl]['id'])
            vti_dict[sitename] = vti_list    
    print(vti_dict)
    return(vti_dict)


def get_sites_state_proxy(proxy,user="",pw=""):
    ''' get the snmp site state information (if.location) from the proxy cache'''
    r = rq.get(proxy + '/api/sites_state', auth=(user,pw))
    if r.status_code == 200:
        return json.loads(r.content)
    else:
        return []

def find_tunnel_relationships(sitedf,region=0):
    ''' using the site data frame, derive the tunnel relationships 
        currently this implementation just derives the hub and spoke relationships 
        and provides a list of tuples that indicate spoke to hub connections. 
        this implementation does not handle dual-hub ( bug in SCM rest api) and 
        it does not enumerate the full mesh link members
        '''
    leaflist = []
    spokes = []
    mesh_nodes = []
    r = []
    if len(sitedf) < 1:
        return r

    #based on the generated site list we should change the center of focus 
    (mid_lat, mid_lon) = latlon_midpoint(sitedf,region)
    # for global networks, this calculation although mathamatically correct is not pleasing so limit center to no be about 50 degrees of latitde
    if (mid_lat > 50):
        mid_lat = 50
    if (mid_lat < -50):
        mid_lat = -50

    # for all the site entries find elements that have reference entried in their leaf attribute
    # add them the ll list
    # this will be all the spoke links. 
    for s in sitedf.index:
        if region == 0:
            if len(sitedf.loc[s]['leafs']) > 0 :
                leaflist.append((s,sitedf.loc[s]['leafs']))
        else:
         if sitedf.loc[s]['region'] == region :
            if len(sitedf.loc[s]['leafs']) > 0 : 
                leaflist.append((s,sitedf.loc[s]['leafs']))

    # for each of the entries on this list, 
    # derive the site/city information and also get the 
    # lat/lon entries for both ends of the link 
    # add these to the return list r
    for a in leaflist:
        (hub,spokelist) = a
        h_city = sitedf.loc[hub]['site']
        for spoke in spokelist:
            spokes.append(spoke)
            s_city =sitedf.loc[spoke]['site']
            r.append(((h_city,sitedf.loc[hub]['lat'],sitedf.loc[hub]['lon']),
                      (s_city,sitedf.loc[spoke]['lat'],sitedf.loc[spoke]['lon'])))
    #
    # derive full mesh but draw it to the center triangle ( make this the regional center later.)
    # 
    for m in sitedf.index:
        if region == 0:
            if m not in spokes:
                m_city = sitedf.loc[m]['site']
                r.append((('Center',mid_lat,mid_lon),
                        (m_city,sitedf.loc[m]['lat'],sitedf.loc[m]['lon'])))
        else:
            if m not in spokes:
                if sitedf.loc[m]['region'] == region :
                    m_city = sitedf.loc[m]['site']
                    r.append((('Center',mid_lat,mid_lon),
                            (m_city,sitedf.loc[m]['lat'],sitedf.loc[m]['lon'])))
    return r



def scattermapbox_line(a_lat, a_lon, z_lat, z_lon, color='rgb(0, 255, 0)'):
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

def generate_sites(green_df, red_df, region=0):
    '''region=0 is all sites, create the mapbox marker defintions for the sites'''
    if region == 0:
        if len(red_df) > 0:
            rl = {                                                     
                'lat': red_df['lat'],
                'lon': red_df['lon'],
                'type': 'scattermapbox',
                'mode':'markers',
                'marker': { 'size':10, 'color': 'rgb(255, 0, 0)' },
                'text': red_df['site']
            }
        else:
            rl = {}
        if len(green_df) > 0:   
            gl = {                                                     
                'lat': green_df['lat'],
                'lon': green_df['lon'],
                'type': 'scattermapbox',
                'mode':'markers',
                'marker': { 'size':10, 'color': 'rgb(0, 255, 0)' },
                'text': green_df['site']
            }
        else:
            gl = {}
    else:
        if len(red_df) > 0:
            rl = {                                                     
                'lat': red_df.loc[red_df['region'] == region]['lat'],
                'lon': red_df.loc[red_df['region'] == region]['lon'],
                'type': 'scattermapbox',
                'mode':'markers',
                'marker': { 'size':10, 'color': 'rgb(255, 0, 0)' },
                'text': red_df['site']
            }
        else: 
            rl = {}
        if len(green_df) > 0: 
            gl = {                                                     
                'lat': green_df.loc[green_df['region'] == region]['lat'],
                'lon': green_df.loc[green_df['region'] == region]['lon'],
                'type': 'scattermapbox',
                'mode':'markers',
                'marker': { 'size':10, 'color': 'rgb(0, 255, 0)' },
                'text': green_df['site']
            }
        else: 
            gl = {}
    return rl, gl

def latlon_midpoint(sitedf, region=0):
    ''' see http://www.geomidpoint.com/calculation.html, 
        figure out the gepgraphical center of gravity for the sites in the desired region
        (region == 0 means all sites) and return this lat/lon cordinate so it may be used
        to center the map'''
    if len(sitedf) < 1:
        return(0,0)
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


    
