
import pandas as pd

def gendict():
    ''' create a dictionary that maps a set of city names into a set of lat/lon values'''
    gpsdf = pd.read_csv('cities_degs.csv')
    d = dict()
    for index, row in gpsdf.iterrows():
        s = row['city']
        s.replace(" ","_")
        d[s] = { 'lat': row['lat'], 'lon': row['lon'] }
    return d
