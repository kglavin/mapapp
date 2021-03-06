#
# Proxy cache that stores a set of data stuctures that are polled or derived from the SCM instnaces. 
# 
# subsytems may 'get' the data or 'post' the data for others to 'get'
#

from scm_api import sitedf, nodedf, eventdf, sites_snmpdf, uplinkdf,sitelinksdf,  init_sitedf, init_nodedf, init_eventdf,init_sites_snmp, init_sitelinksdf, init_uplinkdf
from flask import Flask, url_for
from flask import request, Response
import pandas as pd
import json


app = Flask(__name__)
globals()['sitedf'] = init_sitedf()
globals()['nodedf'] = init_nodedf()
globals()['eventdf'] = init_eventdf()
globals()['sites_snmpdf'] = init_sites_snmp()
#globals()['sitelinksdf'] = init_sitelinksdf()
sites_state = ''
sitelinks = ''

@app.route('/')
def api_root():
    return 'proxy api for SCM data'

#
#  The site structures
#
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
            return "415"
    elif request.method == 'DELETE':
            globals()['sitedf'] = init_sitedf()
            return "200"

# 
# The SNMP host details 
# 
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
            return "415"
    elif request.method == 'DELETE':
            globals()['sites_snmpdf'] = init_sites_snmp()
            return "200"
#
# slitelinks
# 

@app.route('/api/sitelinks',methods = ['GET', 'POST','DELETE'])
def api_sitelinks():
    if request.method == 'GET':
        s = globals()['sitelinks']
        resp = Response(s, status=200, mimetype='application/json')
        resp.headers['Link'] = '/api/sitelinks'
        return resp
    elif request.method == 'POST':
        if request.content_type == 'application/json':
            globals()['sitelinks'] = request.json
            return "200"
        else:
            return "415"
    elif request.method == 'DELETE':
            globals()['sitelinks'] = ''
            return "200"

# 
# The site status details 
# 
@app.route('/api/sites_state',methods = ['GET', 'POST','DELETE'])
def api_sites_state():
    if request.method == 'GET':
        s = globals()['sites_state']
        resp = Response(s, status=200, mimetype='application/json')
        resp.headers['Link'] = '/api/sites_state'
        return resp
    elif request.method == 'POST':
        if request.content_type == 'application/json':
            globals()['sites_state'] = request.json
            return "200"
        else:
            return "415"
    elif request.method == 'DELETE':
            globals()['sites_state'] = ''
            return "200"

#
#  Node details
# 
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
            return "415"
    elif request.method == 'DELETE':
            globals()['nodedf'] = init_nodedf()
            return "200"
#
# the SCM event logs 
#
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
            return "415"
    elif request.method == 'DELETE':
            globals()['nodedf'] = init_eventdf()
            return "200"

if __name__ == '__main__':

    app.run(debug=True, host='127.0.0.1', port='8040')
