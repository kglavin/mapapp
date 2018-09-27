import os
import datetime
import time
import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output, State
import pandas as pd
import netrc
import scm as scm
from scm_api import sitedf, nodedf, eventdf, get_sites, get_nodes, get_eventlogs, generate_tunnels, generate_sites,find_tunnel_relationships,latlon_midpoint
from scmbase_html import heading_html, footer_html
from interface_graphing import query_scmdata

app = dash.Dash(__name__)
# needed to keep dash happy about complex dependancies with multi-page app.
app.config.supress_callback_exceptions = True

def generate_table(dataframe, max_rows=10):
    return html.Table(
        # Header
        [html.Tr([html.Th(col) for col in dataframe.columns])] +

        # Body
        [html.Tr([
            html.Td(dataframe.iloc[i][col]) for col in dataframe.columns
        ]) for i in range(min(len(dataframe), max_rows))]
    )

def traffic_html(sitedf):
    sites = sitedf['site'].tolist()
    return html.Div( children = [  
                html.Div(
                    dcc.Dropdown(
                      id='if-stats-site',
                      options=[{'label': i, 'value': i} for i in sites],
                      value='Albuquerque'
                    )),
                    dcc.Graph(id='if-stats-graph')
                ],
                className="twelve columns"
           )

def event_html():
    return html.Div([
                html.H4(children='Event Log'),
                generate_table(eventdf,500),]
            )

def map_html():
    opts = [ {'label':'All Sites', 'value': 0} ]
    opts.extend([{'label': 'Region '+str(i), 'value': i} for i in globals()['regions']])
    return html.Div( children = [  
                html.Div(
                    dcc.Dropdown(
                        id='map-refresh',
                        options=opts,
                        value=0
                    ),
                ),
                dcc.Graph(id='sites-map')
                ],
                className="twelve columns"
           )

app.layout = html.Div([
    heading_html(),
    dcc.Location(id='url', refresh=False),
    html.Div([
        dcc.Link(html.Button('home',    id='home_page'),    href='/'),
        dcc.Link(html.Button('map',     id='map_page'),     href='/map_page'),
        dcc.Link(html.Button('traffic', id='traffic_page'), href='/traffic_page'),
        dcc.Link(html.Button('event',   id='event_page'),   href='/event_page'),
        ]),
    html.Br(),
    html.Div(id='page-content'),
    footer_html()

])

@app.callback(dash.dependencies.Output('sites-map', 'figure'),
              [dash.dependencies.Input('map-refresh', 'value')])
def gen_map(value):
    tun_list = generate_tunnels(sitedf,region=value)
    tun_list.append(generate_sites(sitedf, region=value))
    #TODO: based on the generated site list we should change the center of focus 
    #TODO: can we focus the zoom of the map to just contain the points in the set?
    (mid_lat, mid_lon) = latlon_midpoint(sitedf,region=value)

    figure={       
            'data': tun_list,
            'layout': {   
                'title': 'Status Map',
                'showlegend': False,
                'height': 720,
                'mapbox': { 'accesstoken': mapbox_access_token,
                            'style': 'mapbox://styles/kglavin/cjgzfhh2900072slet6ksq66d'
                    },
                'layers': [],
                'center': dict(lat=0,lon=0,),
                'margin': {                                                                                                
                        'l': 5, 'r': 5, 'b': 5, 't': 25
                },                                                                        
            }
    } 
    return figure


@app.callback(dash.dependencies.Output('if-stats-graph', 'figure'),
              [dash.dependencies.Input('if-stats-site', 'value')])
def gen_if_stats_graphs(value):
    figure = {}
    qd = {'id':value, 'if_name':'eth0', 'period':'1h'}
    data = query_scmdata("ifstats", query_data=qd)
    derived_data = pd.DataFrame()
    if data.size > 0:
        data['in_octets_rate'] = pd.to_numeric(data['in_octets'], errors='coerce').diff()
        data['out_octets_rate'] = pd.to_numeric(data['out_octets'], errors='coerce').diff()
        figure={
            'data': [{
                    'x': data.index,
                    'y': data['in_octets_rate'],
                    'name': 'in_octets rate',
                    'mode':'lines',
                    'marker': {'size': 2}
                },
                {
                    'x': data.index,
                    'y': data['out_octets_rate'],
                    'name': 'out_octets rate',
                    'mode':'lines',
                    'marker': {'size': 2}
                },
                ]
        }
    return figure

@app.callback(dash.dependencies.Output('page-content', 'children'),
              [dash.dependencies.Input('url', 'pathname')])
def display_page(pathname):
    if pathname is None:
        r = html.Div('/')
    elif pathname == '/':
        r = html.Div("/home_page")
    else:
        if pathname == '/map_page':
            r = map_html()
        if pathname == '/traffic_page':
            r = traffic_html(sitedf)
        if pathname == '/event_page':
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
    regions = []


    netrc = netrc.netrc()

    region = 1
    for host in hosts:
        authTokens = netrc.authenticators(host)
        user = authTokens[0]
        users.append(user)
        pw = authTokens[2]
        regions.append(region)
        get_sites(sitedf, realm, user, pw, region)
        get_nodes(nodedf, sitedf, realm, user, pw,region)
        get_eventlogs(eventdf,realm,user,pw,region) 
        region += 1

    
    app.run_server(debug=True, host='0.0.0.0')