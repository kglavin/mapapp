
import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output, State
from scmbase_html import heading_html, footer_html
from scm_api import get_sites, get_nodes, get_eventlogs, generate_tunnels, generate_sites
import datetime
import time
import pandas as pd
import scm as scm
import gpslocation as gps
import netrc
import os
from interface_graphing import query_scmdata


app = dash.Dash(__name__)
sitedf = pd.DataFrame([],  columns =  ['site', 'lat', 'lon','leafs'])
nodedf = pd.DataFrame([],  columns =  ['site','serial','router_id'])
eventdf = pd.DataFrame([],  columns =  ['Time','utc', 'Message', 'Severity'])

app.layout = html.Div([
    heading_html(),
    dcc.Location(id='url', refresh=False),
    html.Div([
        dcc.Link(html.Button('home', id='home_page'),href='/'),
        dcc.Link(html.Button('map', id='map_page'),href='/map_page'),
        dcc.Link(html.Button('traffic', id='traffic_page'),href='/traffic_page'),
        dcc.Link(html.Button('event', id='event_page'),href='/event_page'),
        ]),
    html.Br(),
    html.Div(id='page-content'),
    footer_html()

])

def generate_table(dataframe, max_rows=10):
    return html.Table(
        # Header
        [html.Tr([html.Th(col) for col in dataframe.columns])] +

        # Body
        [html.Tr([
            html.Td(dataframe.iloc[i][col]) for col in dataframe.columns
        ]) for i in range(min(len(dataframe), max_rows))]
    )

def traffic_html():
    sites = [ 'Kansas', 'Albuquerque', 'Memphis']
    qd = {'id':'Albuquerque', 'if_name':'eth0', 'period':'1h' }
    data = query_scmdata("ifstats", query_data=qd)
    return html.Div( children = [  
                  html.Div(
                    dcc.Dropdown(
                      id='if-stats-site',
                      options=[{'label': i, 'value': i} for i in sites],
                      value='Sites'
                    )),
                dcc.Graph(
                    id='if-stats-interactions',
                    figure={
                        'data': [
                         {
                                'x': data.index,
                                'y': data['in_octets'],
                                'name': 'in_octets',
                                'mode':'lines+markers',
                                'marker': {'size': 6}
                         },
                         {
                                'x': data.index,
                                'y': data['out_octets'],
                                'name': 'out_octets',
                                'mode':'lines+markers',
                                'marker': {'size': 6}
                         },
                        ]
                    }
                )],
                className="twelve columns"
           )

def event_html():
    return html.Div([
                html.H4(children='Event Log'),
                generate_table(eventdf,500),]
            )

def map_html():
    return html.Div([
                html.Div(
                className="twelve columns",
                children=[ dcc.Graph(      
                            id='graph',          
                            figure={       
                                'data': [ generate_tunnels(),generate_sites(sitedf)],
                                'layout': {   
                                    'title': 'Sites',
                                    'showlegend': False,
                                    'mapbox': { 'accesstoken': mapbox_access_token,
                                                'style': 'mapbox://styles/kglavin/cjgzfhh2900072slet6ksq66d'
                                    },
                                    'layers': [],
                                    'center': dict(lat=0,lon=-180,),
                                    'margin': {                                                                                                
                                        'l': 5, 'r': 5, 'b': 5, 't': 25
                                    },                                                                        
                                }
                            }         
                            ),
                        ]        
            )],
            style={
                'height':600,
                'float': 'center',
                'position': 'relative',
            })

@app.callback(dash.dependencies.Output('page-content', 'children'),
              [dash.dependencies.Input('url', 'pathname')])
def display_page(pathname):
    if pathname is None:
        r = html.Div('/')
    elif pathname in '/':
        r = html.Div("/home_page")
    else:
        if pathname in '/map_page':
            r = map_html()
        if pathname in '/traffic_page':
            r = traffic_html()
        if pathname in '/event_page':
            r = event_html()
    return r

app.css.append_css({
    'external_url': 'https://codepen.io/chriddyp/pen/bWLwgP.css'
})

@app.callback(Output('live-update-text', 'children'),
                [Input('interval-component', 'n_intervals')])
def update_time(n):
    t = datetime.datetime.now()
    return  ['Time: {}'.format(t)]

if __name__ == '__main__':
    mapbox_access_token = "pk.eyJ1Ijoia2dsYXZpbiIsImEiOiJjamd6ZjgzZDkwZWJlMnFyNG1wN3ZlMXVwIn0.qygVV7-zi8IMX8wyxawEpA"
    #mapbox_access_token = os.environ.get('MAPBOX_ACCESS_TOKEN', 'mapbox-token')

    realm = 'https://catfish3.riverbed.cc'
    hosts = ['kglavin-us', 'kglavin-eur', 'kglavin-asia' ]
    users = []
    pw=[]

    gpsdict = gps.gendict()
    netrc = netrc.netrc()

    for host in hosts:
        authTokens = netrc.authenticators(host)
        user = authTokens[0]
        users.append(user)
        pw = authTokens[2]
        get_sites(sitedf, realm, user, pw)
        get_nodes(nodedf, sitedf, realm, user, pw)
        get_eventlogs(eventdf,realm,user,pw) 

    server = app.server

    app.run_server(debug=True, host='0.0.0.0')