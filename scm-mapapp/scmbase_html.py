#
# routines to generate basic html structures for use in the application, 
# standard header and footer. 
#
import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output, State

def heading_html():
    return html.Div([html.Div(
            [
                html.H1(
                    'SteelConnect Global Networks Overview.',
                    className='eight columns',
                    style={
#                        'color': colors['text'],
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
        ],
        className='twelve columns'
        )

def footer_html():
    return  html.Footer([html.Div([
                    html.Div("this is the footer")],
                    className='ten columns',
                    style={
                       'height': 70,
                       'color': 'blue',
#                       'backgroundColor': '#FF6900'
                    }),
                    html.P(id='live-update-text',
                        style={ 
                                'height': 70,
                                'text-align': 'right',
                                'color': 'blue',
#                                'backgroundColor': '#FF6900'
                    }),
                    dcc.Interval(
                        id='interval-component',
                        interval=5000, # in milliseconds
                        n_intervals=0),
            ])
