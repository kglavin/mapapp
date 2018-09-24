import datetime
import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output, State
import requests as rq
import json
import pandas as pd
import scm as scm
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
realm = 'https://catfish3.riverbed.cc'
hosts = ['kglavin-us', 'kglavin-eur', 'kglavin-asia' ]
users = []
pw=[]

colors = {
    'background': '#111111',
    'text': '#7FDBFF'
}


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


def orgs_html(users):
    return html.Div(
           [
               html.H5(
                   realm,
                   id='realm',
                   className='two columns'
               ),
               html.H5(
                   [str(n)+' ' for n in users],
                   id='admins',
                   className='eight columns',
                   style={'text-align': 'center'}
               ),
               html.H5( id='live-update-text',
                        className='two columns',
                        style={'text-align': 'right'})
           ],
           className='row'
        )

def map_html(sitedf):
    return html.Div(
            className="twelve columns",
            children=[ dcc.Graph(      
                id='graph',          
                figure={       
                    'data': [ generate_tunnels(),generate_sites(sitedf)],
                    'layout': {   
                        'title': 'Sites',
                        'showlegend': False,
                        'mapbox': { 'accesstoken': mapbox_access_token,
                                    'style': 'mapbox://styles/kglavin/cjgzfhh2900072slet6ksq66d'},
                                    'layers': [],
                                    'center': dict(lat=0,lon=-180,),
                        'margin': {                                                                                                
                            'l': 5, 'r': 5, 'b': 5, 't': 25
                        },                                
                    }                                     
                }         
            ),]        
        )

def heading_html():
    return html.Div(
            [
                html.H1(
                    'SteelConnect Global Networks Overview.',
                    className='eight columns',
                    style={
                        'color': colors['text'],
#                        'backgroundColor': colors['background']
                    },     
                ),
                html.A([
                    html.Img(
                        src='https://www.riverbed.com/content/dam/riverbed-www/en_US/Images/fpo/logo_riverbed_orange.png?redesign=true',
                         className='one columns',
                         style={
                            'width':160,
                            'float': 'right',
                            'position': 'relative',
                        })
                    ], href='https://www.riverbed.com'),
            ],
            className='row'
        )

def appliances_html(nodedf):
    return html.Div( children=[
                html.H4(children='Appliances'),
                generate_table(nodedf,100),],
                className="four columns"
            )

def eventlog_html(eventdf):
    return html.Div( children=[
                html.H4(children='Event Log'),
                generate_table(eventdf,500),],
                className="eight columns",
            )


def generate_tunnels():
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
            'marker':{ 'size':14, 'color': 'rgb(0, 225, 0)' },
            'text': sitedf['site']
    }
def app_html(users, sitedf, nodedf, eventdf):
    return html.Div( 
        children = [
        heading_html(),
        orgs_html(users),
        map_html(sitedf),
        html.Div(
            children=[        
            appliances_html(nodedf),
            eventlog_html(eventdf)]
            ),
        dcc.Interval(
            id='interval-component',
            interval=60000, # in milliseconds
            n_intervals=0
        )
        ]
    )

if __name__ == '__main__':
    gpsdict = gps.gendict()
    netrc = netrc.netrc()

    app = dash.Dash(__name__)
    server = app.server

    sitedf = pd.DataFrame([],  columns =  ['site', 'lat', 'lon','leafs'])
    nodedf = pd.DataFrame([],  columns =  ['site','serial','router_id'])
    eventdf = pd.DataFrame([],  columns =  ['Time','utc', 'Message', 'Severity'])

    def serve_layout():
        return app_html(users, sitedf, nodedf, eventdf)

    for host in hosts:
        authTokens = netrc.authenticators(host)
        user = authTokens[0]
        users.append(user)
        pw = authTokens[2]
        get_sites(sitedf, realm, user, pw)
        get_nodes(nodedf, sitedf, realm, user, pw)
        get_eventlogs(eventdf,realm,user,pw) 

    app.layout = serve_layout

    app.css.append_css({
        'external_url': 'https://codepen.io/chriddyp/pen/bWLwgP.css'
    })

    @app.callback(Output('live-update-text', 'children'),
                [Input('interval-component', 'n_intervals')])
    def update_time(n):
        t = datetime.datetime.now()
        return  ['Time: {}'.format(t)]      

    app.run_server(debug=True, host='0.0.0.0')
