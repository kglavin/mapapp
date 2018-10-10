#
# dash/flask based dashboard to present data that is derived from a set of SCM instances via rest
# interfaces 
# or from SNMP data polled from the appliances associated with those SCM instances
# 

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
from scm_api import sitedf,init_sitedf, nodedf, eventdf, get_sites_proxy, get_nodes_proxy, get_eventlogs_proxy, generate_tunnels, generate_sites,find_tunnel_relationships,latlon_midpoint, get_sites_state_proxy
from scmbase_html import heading_html, footer_html
from interface_graphing import query_scmdata

app = dash.Dash(__name__)
# needed to keep dash happy about complex dependancies with multi-page app.
app.config.supress_callback_exceptions = True

#
# Home page
#
def home_regions():
    r = html.Div( children = [
            html.H3('Managing [3] Regions'),
            html.A(html.Button('Launch Region1 SCM'),href='https://catfish3.riverbed.cc/admin/kglavin-us'),
            html.A(html.Button('Launch Region2 SCM'),href='https://catfish3.riverbed.cc/admin/kglavin-eur'),
            html.A(html.Button('Launch Region3 SCM'),href='https://catfish3.riverbed.cc/admin/kglavin-asia'),
            html.Br(),
        ]
        )
    return r
def home_nodes():
    r = html.Div( children = [
            html.H3('Managing [x] Nodes '),
            html.P('In Region 1,   36 Nodes are Ok/Up,  4 Nodes are Alarming/Down'),
            html.P('In Region 2,   30 Nodes are Ok/Up,  3 Nodes are Alarming/Down'),
            html.P('In Region 1,   40 Nodes are Ok/Up,  0 Nodes are Alarming/Down')
            ], className="twelve columns"
            )
    return r
def home_traffic():
    r = html.Div("graphs here")
    r = html.Div( children = [
            html.H3('Traffic Summary '),
            html.Div(children = [ html.P('In Region 1, intra, inter and total traffic'),
                html.Div(children = [dcc.Graph(id='region1-intra-traffic')], className='three columns'),
                html.Div(children = [dcc.Graph(id='region1-inter-traffic')], className='three columns'),
                html.Div(children = [dcc.Graph(id='region1-total-traffic')], className='three columns')
                ], className="row"
                ),
            html.Div(children = [ html.P('In Region 2, intra, inter and total traffic'),
                html.Div(children = [dcc.Graph(id='region2-intra-traffic')], className='three columns'),
                html.Div(children = [dcc.Graph(id='region2-inter-traffic')], className='three columns'),
                html.Div(children = [dcc.Graph(id='region2-total-traffic')], className='three columns')
                ], className="twelve columns"
                ),
            html.Div(children = [ html.P('In Region 3, intra, inter and total traffic'),
                html.Div(children = [dcc.Graph(id='region3-intra-traffic')], className='three columns'),
                html.Div(children = [dcc.Graph(id='region3-inter-traffic')], className='three columns'),
                html.Div(children = [dcc.Graph(id='region3-total-traffic')], className='three columns')
                ], className="twelve columns"
                )]
        )
    return r

def home_html():
    r  =   html.Div( children = [ 
                    html.Div( children=home_regions(),className='row'),
                    html.Div( children=home_nodes(),className='row'),
                    html.Div( children=home_traffic(),className='row')],
                    className="twelve columns")
    return r

###
# Traffic Page -- this allows for interface and tunnel data to be presented in graphical format
###
def traffic_dropdowns(sitedf):
    if len(sitedf) > 0:
        sites = sitedf['site'].tolist()
    else:
        sites = ['nosite']
    interfaces = [ 0,1,2,3,4]
    tun=['eth','tun']
    duration = [ '1h', '3h','30m', '5m', '24h', '7d']
    gtype=['Packets','Octets']

    d1 = dcc.Dropdown(id='if-stats-site',
                      options=[{'label': i, 'value': i} for i in sites],
                      value='Albuquerque',
                      className='three columns')
    d2 = dcc.Dropdown(id='if-stats-tun',
                      options=[{'label': i, 'value': i } for i in tun ],
                      value='eth',
                      className='one column')
    d3 = dcc.Dropdown(id='if-stats-eth',
                      options=[{'label': "if-"+str(i), 'value': i } for i in interfaces ],
                      value='0',
                      className='three columns')
    d4 = dcc.Dropdown(id='if-stats-duration',
                      options=[{'label': "Past Duration: "+i, 'value': i } for i in duration ],
                      value='1h',
                      className='three columns')
    d5 = dcc.Dropdown(id='if-stats-packets',
                      options=[{'label': "Type: "+i, 'value': i } for i in gtype ],
                      value='Octets',
                      className='three columns')
    b1  = dcc.Link(html.Button('Refresh',   id='graph_refresh', className='one column'))

  #  i1 = dcc.Interval(
  #                      id='interval-graph',
  #                      interval=30000, # in milliseconds
  #                      n_intervals=0)

    return [ d1,d2,d3,d4,d5]

def traffic_html(sitedf):
    return html.Div(children = [ html.Div( children=traffic_dropdowns(sitedf),className='row'),
                                dcc.Graph(id='if-stats-graph')],
                    className="twelve columns")

###    
# Event page -- provides a table view of the event log that is polled from 
# the SCM instances 
###
def generate_table(dataframe, max_rows=10):
    return html.Table(
        # Header
        [html.Tr([html.Th(col) for col in dataframe.columns])] +

        # Body
        [html.Tr([
            html.Td(dataframe.iloc[i][col]) for col in dataframe.columns
        ]) for i in range(min(len(dataframe), max_rows))]
    )

def event_html():
    return html.Div(children=[
                html.H4('Event Log'),
                generate_table(eventdf,500),]
            )

###
# MAP page -- displays a map with an overlay of the site locations 
# and the interconnectivity between sites 
# filtering and scoping via dropdown is provided 
# all sites or regional views, currently the sites for each individual SCM 
# instance are each assigned to a unique region
###
def map_dropdowns(regions):
    opts = [ {'label':'All Sites', 'value': 0} ]
    opts.extend([{'label': 'Region '+str(i), 'value': i} for i in regions])

    d1 = dcc.Dropdown(id='map-refresh',
                        options=opts,
                        value=0)
    return [ d1 ]


def map_html(regions):
    return html.Div( children = [  
                html.Div( children=map_dropdowns(regions), className='row'),
                dcc.Graph(id='sites-map')
                ],
                className="twelve columns"
           )

###
# Top Level page -- navigation buttons to the other main pages 
###
def scm_buttons():
    b1 = dcc.Link(html.Button('home',    id='home_page'),    href='/')
    b2 = dcc.Link(html.Button('map',     id='map_page'),     href='/map_page')
    b3 = dcc.Link(html.Button('traffic', id='traffic_page'), href='/traffic_page')
    b4 = dcc.Link(html.Button('event',   id='event_page'),   href='/event_page')
    return [ b1, b2, b3, b4]

def scm_layout():
    r =   html.Div(children =[
                    heading_html(),
                    dcc.Location(id='url', refresh=False),
                    html.Div(children= scm_buttons()),
                    html.Br(),
                    html.Div(id='page-content'),
                    footer_html()
                    ])
    return r

app.layout = scm_layout()

#
# update the map page based on the map criteria being refreshed ( changing or reslecting a site scope)
#
@app.callback(dash.dependencies.Output('sites-map', 'figure'),
              [dash.dependencies.Input('map-refresh', 'value')])
def gen_map(region):
    ## for each map update hit the local proxy to get the most recently polled sitesdf
    # this may still be stale data on the proxy but its responsive data.
    green_df = init_sitedf()
    red_df = init_sitedf()
    df = get_sites_proxy(globals()['proxy'])

    #based on the generated site list we should change the center of focus 
    (mid_lat, mid_lon) = latlon_midpoint(df,region)

    site_state_list = get_sites_state_proxy(globals()['proxy'])
    # calculate the correct fm state (color for the states based on the sites_state values
    #print(type(site_state_list),site_state_list) 'site', 'lat', 'lon','leafs','region', 'fm_state'])
    for li in site_state_list:
        if li['id'] is not 'Dead':
            if li['site'] in df.index:
             green_df = green_df.append(df.loc[li['site']])
             #df.drop(df.loc[li['site']], inplace=True)
            else:
                print(li['site'], " not in index for gen_map")
        else:
            if li['site'] in df.index:  
                red_df = red_df.append(df.loc[li['site']])
            else:
                print(li, "Dead -  not in index for gen_map")

    tun_list = generate_tunnels(df,region)
    rl, gl = generate_sites(green_df, df, region)
    tun_list.append(rl)
    # drap green last so its the top layer of dots. 
    tun_list.append(gl)
    
    #TODO: can we focus the zoom of the map to just contain the points in the set?
    # for global networks, this calculation although mathamatically correct is not pleasing so limit center to no be about 50 degrees of latitde
    if (mid_lat > 50):
        mid_lat = 50
    if (mid_lat < -50):
        mid_lad = -50

    mbox = { 'accesstoken': mapbox_access_token,
             'style': 'mapbox://styles/kglavin/cjgzfhh2900072slet6ksq66d',
             'center': dict(lat=mid_lat,lon=mid_lon,),
             'layers': [],
             'minZoom': 0
           }

    #if region > 0:
    #    mbox['zoom'] = 3

    
    # This is the midpoint drawn as a triangle on the map -- 
    # TODO, will use this ( or another icon as the place to show a full mesh terminating)
    m_point = {
            'lat': [mid_lat],
            'lon': [mid_lon],
            'type': 'scattermapbox',
            'mode':'markers',
            'marker':{ 'size':15, 'symbol':'triangle', 'color': 'rgb(0, 0, 255)' },
            'text': "Center"
        }
    tun_list.append(m_point)

    figure={       
            'data': tun_list,
            'layout': {   
                'title': 'Status Map',
                'showlegend': False,
                'height': 720,
                'mapbox': mbox,
                'margin': {                                                                                                
                        'l': 5, 'r': 5, 'b': 5, 't': 25
                },                                                                        
            }
    } 
    return figure

#
# graph statistics material is queried and formatted into appropriate 
# format when the filter/scope drop downs are manipulated
#

def gen_if_stats_data(site,tun,eth,duration,packets):
    qd = {'id':site, 'if_name':str(tun)+str(eth), 'period':duration}
    data = query_scmdata("ifstats", query_data=qd)

    if data.size > 0:
        data['deltaT'] = data.index.to_series().diff().dt.total_seconds()
        if packets in 'Octets':
            data['in'] = pd.to_numeric(data['in_octets'], errors='coerce').diff().clip(lower=0)/data['deltaT']*8
            data['out'] = pd.to_numeric(data['out_octets'], errors='coerce').diff().clip(lower=0)/data['deltaT']*8* -1
            data['in_rolling']= data['in'].rolling(3).mean()
            data['out_rolling']= data['out'].rolling(3).mean()
        else:
            data['in'] = pd.to_numeric(data['in_unicast'], errors='coerce').diff().clip(lower=0)/data['deltaT']
            data['out'] = pd.to_numeric(data['out_unicast'], errors='coerce').diff().clip(lower=0)/data['deltaT']*-1
            data['in_rolling']= data['in'].rolling(3).mean()
            data['out_rolling']= data['out'].rolling(3).mean()
    return data

#dash.dependencies.Input('graph_refresh', 'value')
#dash.dependencies.Input('interval-graph', 'n_intervals') 

@app.callback(output=dash.dependencies.Output('if-stats-graph', 'figure'),
              inputs=[dash.dependencies.Input('if-stats-site', 'value'),
              dash.dependencies.Input('if-stats-tun', 'value'),
              dash.dependencies.Input('if-stats-eth', 'value'),
              dash.dependencies.Input('if-stats-duration', 'value'),
              dash.dependencies.Input('if-stats-packets', 'value'),
                           
              ])
def gen_if_stats_graphs(site,tun,eth,duration,packets):
        data=gen_if_stats_data(site,tun,eth,duration,packets)
        if packets == 'Octets':
            packets = 'Bits'
        if len(data) > 0:
            # four lines on the graph ( and in and an out) and rolling average
            figure={
                'data': [
                    #{
                    #'x': data.index,
                    #'y': data['in'],
                    #'name': 'In '+packets +'/s',
                    #'mode':'lines',
                    #'line': {
                    #    'shape':'spline',
                    #    'width':1
                    #    },
                    #'marker': {'size': 2}
                    #},
                    #{
                    #'x': data.index,
                    #'y': data['out'],
                    #'name': 'Out '+packets+'/s',
                    #'mode':'lines',
                    #'line': {
                    #    'shape':'spline',
                    #    'width':1
                    #    },
                    #'marker': {'size': 2}
                    #},
                    {
                    'x': data.index,
                    'y': data['in_rolling'],
                    'name': 'RA In '+packets+'/s',
                    'mode':'lines',
                    'line': {
                        'shape':'spline',
                        'width':2
                        },
                    'marker': {'size': 4}
                    },
                    {
                    'x': data.index,
                    'y': data['out_rolling'],
                    'name': 'RA Out '+packets+'/s',
                    'mode':'lines',
                    'line':{
                        'shape':'spline',
                        'width':2
                        },
                    'marker': {'size': 4}
                    }
                    ]
            }
        else: 
            figure = {}
        return figure

#
# Render the correct top level page based on the url that is requested or 
# caused by a refresh/filter/button action
#
@app.callback(dash.dependencies.Output('page-content', 'children'),
              [dash.dependencies.Input('url', 'pathname')])
def display_page(pathname):
    if pathname is None:
        r =home_html() 
    elif pathname == '/':
        r =home_html() 
    else:
        if pathname == '/map_page':
            r = map_html(regions)
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

#
# hardcoded list of SCM instances in this case a single realm is hosting three 
# SCM instances but for scale setups 
# it possible that there would be unique REALM instances for each SCM instance
#
    realm = 'https://catfish3.riverbed.cc'
    hosts = ['kglavin-us', 'kglavin-eur', 'kglavin-asia' ]
    users = []
    pw=[]
    regions = []
    # 
    # a caching server into which an scm_polling backend is periodically posting data 
    # received from the SCM instance via rest 
    # 
    proxy = "http://127.0.0.1:8040"

    # use the netrc machanism to retrieve from the user( on server) the .netrc based credentials to access 
    # the scm instance. 
    netrc = netrc.netrc()

    # region starts at 1 for SCM istances, region == 0 is used to indicate all regions in 
    # the map filtering. 
    region = 1
    for host in hosts:
        authTokens = netrc.authenticators(host)
        user = authTokens[0]
        users.append(user)
        pw = authTokens[2]
        regions.append(region)
        region += 1

    # get the cached information from the scm, the individual pages may refresh this information 
    # on demand as pages are served. 
    sitedf = get_sites_proxy(proxy)
    nodedf = get_nodes_proxy(proxy)
    eventdf = get_eventlogs_proxy(proxy)

    app.run_server(debug=True, host='0.0.0.0')
