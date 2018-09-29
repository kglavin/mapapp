from scm_api import sitedf, nodedf, eventdf, sites_snmpdf, uplinkdf,  init_sitedf, init_nodedf, init_eventdf,init_sites_snmp, init_uplinkdf
from flask import Flask, url_for
from flask import request, Response
import pandas as pd
import json


app = Flask(__name__)
globals()['sitedf'] = init_sitedf()
globals()['nodedf'] = init_nodedf()
globals()['eventdf'] = init_eventdf()
globals()['sites_snmpdf'] = init_sites_snmp()

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
            return "200"
        else:
            return "415 Unsupported Media Type"
    elif request.method == 'DELETE':
            globals()['sitedf'] = init_sitedf()
            return "200"

@app.route('/api/snmp_details',methods = ['GET', 'POST','DELETE'])
def api_snmp_details():
    if request.method == 'GET':
        s = globals()['sites_snmpdf'].to_json(orient='index')
        resp = Response(s, status=200, mimetype='application/json')
        resp.headers['Link'] = '/api/snmp_details'
        return resp
    elif request.method == 'POST':
        if request.content_type == 'application/json':
            globals()['sites_snmpdf'] = pd.read_json(request.get_json(), orient='index')
            return "200"
        else:
            return "415 Unsupported Media Type"
    elif request.method == 'DELETE':
            globals()['sites_snmpdf'] = init_sites_snmp()
            return "200"

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
            return "200"
        else:
            return "415 Unsupported Media Type "
    elif request.method == 'DELETE':
            globals()['nodedf'] = init_nodedf()
            return "200"

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
            return "200"
        else:
            return "415 Unsupported Media Type"
    elif request.method == 'DELETE':
            globals()['nodedf'] = init_eventdf()
            return "200"

if __name__ == '__main__':

    app.run(debug=True, host='127.0.0.1', port='8040')
