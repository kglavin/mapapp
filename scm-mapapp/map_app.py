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
users = ['kglavin-us-bot', 'kglavin-eur-bot', 'kglavin-asia-bot' ]
pw='b0ts'

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
    userlist = ""
    
    for user in users:
        userlist = userlist + user + ','
        r = scm.get('sites', realm, user,pw)
        if r.status_code == 200:
            f = r.json()
            for a in f['items']:
                #print(a)
                p = gpsdict[a['city']]
                lat = p['lat']
                lon = p['lon']
                sitedf.loc[a['id']] = [a['city'], lat, lon]

        r = scm.get('nodes', realm, user,pw)
        if r.status_code == 200:
            f = r.json()
            for a in f['items']:
                city = sitedf.loc[a['site']]['site']
                nodedf.loc[a['id']] = [ city, a['serial'], a['router_id']]         
        
        r = scm.get('eventlogs', realm, user,pw)
        if r.status_code == 200:
            f = r.json()
            for a in f['items']:
                eventdf.loc[a['id']] = [datetime.datetime.fromtimestamp(a['utc']).strftime('%c'),
                                        a['utc'],
                                        a['msg'],
                                        a['severity']]


#    geojson_type_dict=dict(
#            type = 'scattergeo',
#            lat = [ 40.7127, 51.5072 ],
#            lon = [ -74.0059, 0.1275 ],
#            mode = 'lines',
#            line = dict(
#                        width = 2,
#                        color = 'blue',
#                    ),
#        )
    

    geo_type_dict = {
        "type": "geojson",
        "data": {
            "type": "Feature",
            "properties": {},
            "geometry": {
                "type": "LineString",
                "coordinates": [[2, 44.4074], [-89,35 ]],
            }}}

    layers=[dict(sourcetype = 'geojson',
                          source = geo_type_dict,
                          color='rgb(0,0,230)',
                          type = 'line',
                          line=dict(width=1.5),
                    )
                 ]  
                 
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
                   userlist,
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
                    'data': [{                                                     
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
                                    'layers': layers,
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


    app.run_server(debug=True)
