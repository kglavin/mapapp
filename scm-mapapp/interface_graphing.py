from influxdb import DataFrameClient
import pandas as pd
from pytz import timezone



def query_scmdata(measurement, query_data = {'period':'1m', 'limit':'50'}):
    ''' the time series data stored in the influxdb with a currently hardcoded hostname of influxdb, 
    may be queried using this interface. the measurement is the name of the database instance 
    and the query_data dictionary provides a flexibe method of describing a complex query in terms
    of scoping and filtering. 
    items that are added to the query_data dictionary become where clauses in the select statement used 
    to read data from the time series database, additionally a period and result limit clause can be 
    populated
    example query data dictionaries are 
      qd = {'id':'Kansas', 'if_name':'eth0'  } 
        qd = {'id':'Kansas' } 
        qd = {'site':'site-HQ-9759dcfb53b4a9d1', 'if_name':'eth0' } 
        qd = {'status':'1', 'limit':30, 'period':'2m' } 
        qd = {'id':'Kansas', 'if_name':'eth0', 'period':'1h'}


    '''

    client = DataFrameClient(host     = 'influxdb',
                             port     = 8086,
                             database = 'scmdata')

    # standard set of null clauses that may be augmented and made into specific 
    # scoping or filtering clauses through additions to the query_data dictionary
    id_where = ''' ''' 
    if_name_where = ''' ''' 
    site_where = ''' ''' 
    status_where = ''' ''' 
    limit_clause = ''' '''
    period_clause = ''' time > now() - 1m '''


    # using python format strings augment the scoping filters
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

    # if the result has entries format them into a pandas dataframe
    result = client.query(query, chunked=True)
    if len(result) > 0:
        column = next(iter(result))
        data   = result[column]
        data.index = data.index.tz_convert('America/Los_Angeles')
        data.index = data.index.tz_localize(None)
    else:
        # otherwise return an empty dataframe
        data = pd.DataFrame()
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
