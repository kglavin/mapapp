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



if __name__ == '__main__':
    app = dash.Dash(__name__)
    server = app.server

    sitedf = pd.DataFrame([],  columns =  ['site', 'lat', 'lon'])
    nodedf = pd.DataFrame([],  columns =  ['site','serial','router_id'])
    eventdf = pd.DataFrame([],  columns =  ['Time','utc', 'Message', 'Severity'])

    gpsdict = gps.gendict()
    netrc = netrc.netrc()

    for host in hosts:
        authTokens = netrc.authenticators(host)
        user = authTokens[0]
        users.append(user)
        pw = authTokens[2]
        r = scm.get('sites', realm, user,pw)
        if r.status_code == 200:
            f = r.json()
            for a in f['items']:
                #print("############  SITES")
                #print(a)
                p = gpsdict[a['city']]
                lat = p['lat']
                lon = p['lon']
                sitedf.loc[a['id']] = [a['city'], lat, lon]

        r = scm.get('nodes', realm, user,pw)
        if r.status_code == 200:
            f = r.json()
            for a in f['items']:
                #print("############  NODES")
                #print(a)
                city = sitedf.loc[a['site']]['site']
                nodedf.loc[a['id']] = [city, a['serial'], a['router_id']]         
        
        r = scm.get('eventlogs', realm, user,pw)
        if r.status_code == 200:
            f = r.json()
            #print("############  Events")
            for a in f['items']:
                #print(a)
                eventdf.loc[a['id']] = [datetime.datetime.fromtimestamp(a['utc']).strftime('%c'),
                                        a['utc'],
                                        a['msg'],
                                        a['severity']]


    app.layout = html.Div(
        
        children = [
        html.Div(
            [
                html.H1(
                    'SteelConnect Global Networks Overview.',
                    className='eight columns',
                    style={
                        'color': colors['text'],
                        'backgroundColor': colors['background']
                    },     
                ),
                html.Img(
                    src="/logo_riverbed_orange.png",
                    className='one columns',
                    style={
                        'height': '100',
                        'width': '225',
                        'float': 'right',
                        'position': 'relative',
                    },
                ),
            ],
            className='row'
        ),
        html.Div(
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
               html.H5(
                   'Text 3 ',
                   id='year_text',
                   className='two columns',
                   style={'text-align': 'right'}
               ),
           ],
           className='row'
        ),
        html.Div(
            className="twelve columns",
            children=[ dcc.Graph(      
                id='graph',          
                figure={       
                    'data': [ {                                                     
                        'lat': [52.37, 50.12 ],
                        'lon': [4.9 , 8.68 ],
                        'type': 'scattermapbox',
                        'mode':'lines',
                        'line':{ 'size':1, 'color': 'rgb(255, 0, 0)' },
                    },
                    {                                                     
                        'lat': sitedf['lat'],
                        'lon': sitedf['lon'],
                        'type': 'scattermapbox',
                        'mode':'markers',
                        'marker':{ 'size':14, 'color': 'rgb(0, 225, 0)' },
                        'text': sitedf['site']
                    }],
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
        ),
        html.Div(
            children=[        
            html.Div( children=[
                html.H4(children='Appliances'),
                generate_table(nodedf,100),],
                className="four columns"
            ),
            html.Div( children=[
                html.H4(children='Event Log'),
                generate_table(eventdf,500),],
                className="eight columns",
            ),
        ],),
    ],)

    app.css.append_css({
        'external_url': 'https://codepen.io/chriddyp/pen/bWLwgP.css'
    })

    #@app.callback(
    #    Output('lasso', 'children'),
    #    [Input('graph', 'selectedData')])

    #def display_data(selectedData):
    #    return json.dumps(selectedData, indent=2)


    app.run_server(debug=True, host='0.0.0.0')
