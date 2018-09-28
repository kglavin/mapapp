from scm_api import sitedf, nodedf, eventdf, init_sitedf, init_nodedf, init_eventdf
from flask import Flask, url_for
from flask import request, Response
import pandas as pd
import json


app = Flask(__name__)
globals()['sitedf'] = init_sitedf()
globals()['nodedf'] = init_nodedf()
globals()['eventdf'] = init_eventdf()

@app.route('/')
def api_root():
    return 'proxy api for SCM data'

@app.route('/api/sites',methods = ['GET', 'POST','DELETE'])
def api_sites():
    if request.method == 'GET':
        js = globals()['sitedf'].to_json(orient='index')
        resp = Response(js, status=200, mimetype='application/json')
        resp.headers['Link'] = '/api/sites'
        return resp
    elif request.method == 'POST':
        if request.content_type == 'application/json':
            globals()['sitedf'] = pd.read_json(request.get_json(), orient='index')
            return "200 ECHO: POST\n"
        else:
            return "415 Unsupported Media Type ;)"
    elif request.method == 'DELETE':
            globals()['sitedf'] = init_sitedf()
            return "ECHO: DELETE"


@app.route('/api/nodes',methods = ['GET', 'POST','DELETE'])
def api_nodes():
    if request.method == 'GET':
        js = globals()['nodedf'].to_json(orient='index')
        resp = Response(js, status=200, mimetype='application/json')
        resp.headers['Link'] = '/api/nodes'
        return resp
    elif request.method == 'POST':
        if request.content_type == 'application/json':
            globals()['nodedf'] = pd.read_json(request.get_json(), orient='index')
            return "200 ECHO: POST\n"
        else:
            return "415 Unsupported Media Type ;)"
    elif request.method == 'DELETE':
            globals()['nodedf'] = init_nodedf()
            return "ECHO: DELETE"

@app.route('/api/eventlogs',methods = ['GET', 'POST','DELETE'])
def api_eventlogs():
    if request.method == 'GET':
        js = globals()['eventdf'].to_json(orient='index')
        resp = Response(js, status=200, mimetype='application/json')
        resp.headers['Link'] = '/api/eventlogs'
        return resp
    elif request.method == 'POST':
        if request.content_type == 'application/json':
            globals()['eventdf'] = pd.read_json(request.get_json(), orient='index')
            return "200 ECHO: POST\n"
        else:
            return "415 Unsupported Media Type ;)"
    elif request.method == 'DELETE':
            globals()['nodedf'] = init_eventdf()
            return "ECHO: DELETE"

if __name__ == '__main__':

    app.run(debug=True, host='0.0.0.0', port='8040')
