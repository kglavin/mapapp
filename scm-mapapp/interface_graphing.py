from influxdb import DataFrameClient
import pandas as pd
from pytz import timezone



def query_scmdata(measurement, query_data = {'period':'1m', 'limit':'50'}):
    client = DataFrameClient(host     = 'influxdb',
                             port     = 8086,
                             database = 'scmdata')

    id_where = ''' ''' 
    if_name_where = ''' ''' 
    site_where = ''' ''' 
    status_where = ''' ''' 
    limit_clause = ''' '''
    period_clause = ''' time > now() - 1m '''

    for k,v in query_data.items():
        if k  is 'id':
            id_where = f'''id = '{v}'  and '''
        if k is 'if_name':
            if_name_where = f'''if_name = '{v}' and '''
        if k is 'site':
            site_where = f'''site = '{v}' and '''
        if k is 'status':
            status_where = f'''status = '{v}' and '''
        if k is 'limit':
            l = str(v)
            limit_clause = f'''limit {l} '''
        if k is 'period':
            p = str(v)
            period_clause = f'''time > now() - {p} '''

    query = f'''SELECT * FROM {measurement} WHERE {id_where} {if_name_where} {site_where} {status_where} {period_clause} {limit_clause}'''
    print(query)
    result = client.query(query, chunked=True)
    column = next(iter(result))
    
    data   = result[column]
    data.index = data.index.tz_convert('America/Los_Angeles')
    data.index = data.index.tz_localize(None)
    return data



if __name__ == "__main__":

    qd = {'id':'Kansas', 'if_name':'eth0'  } 
    qd = {'id':'Kansas' } 
    qd = {'site':'site-HQ-9759dcfb53b4a9d1', 'if_name':'eth0' } 
    qd = {'status':'1', 'limit':30, 'period':'2m' } 
    #qd = {'id':'Kansas', 'if_name':'eth0', 'period':'1h'}
    data = query_scmdata("ifstats", query_data=qd)
    print(data)
    print(data['in_octets'])
    print(data.index)
