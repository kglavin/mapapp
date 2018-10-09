import os
import datetime
import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output, State
import requests as rq
import json
import pandas as pd
import scm as scm
from scm_api import sitedf, nodedf, uplinkdf, eventdf,sites_snmpdf, get_sites, get_nodes, get_uplinks, get_eventlogs, generate_tunnels, generate_sites,find_tunnel_relationships,latlon_midpoint,gen_sites_snmp
import gpslocation as gps
from geojson import MultiLineString
import netrc

def generate_table(dataframe, max_rows=10):
    return html.Table(
        # Header
        [html.Tr([html.Th(col) for col in dataframe.columns])] +

        # Body
        [html.Tr([
            html.Td(dataframe.iloc[i][col]) for col in dataframe.columns
        ]) for i in range(min(len(dataframe), max_rows))]
    )




mapbox_access_token = "pk.eyJ1Ijoia2dsYXZpbiIsImEiOiJjamd6ZjgzZDkwZWJlMnFyNG1wN3ZlMXVwIn0.qygVV7-zi8IMX8wyxawEpA"
mapbox_access_token = os.environ.get('MAPBOX_ACCESS_TOKEN', 'mapbox-token')

realm = 'https://catfish3.riverbed.cc'
hosts = ['kglavin-us', 'kglavin-eur', 'kglavin-asia' ]
users = []
pw=[]




if __name__ == '__main__':

    gpsdict = gps.gendict()
    netrc = netrc.netrc()


    for host in hosts:
        authTokens = netrc.authenticators(host)
        user = authTokens[0]
        users.append(user)
        pw = authTokens[2]
        get_sites(sitedf, realm, user, pw)
        get_nodes(nodedf, sitedf, realm, user, pw)
        #get_eventlogs(eventdf,realm,user,pw) 
        get_uplinks(uplinkdf,sitedf, realm, user, pw)
        
    gen_sites_snmp(sites_snmpdf,uplinkdf)
    print(sites_snmpdf)

