
import pandas as pd

def gendict():
    gpsdf = pd.read_csv('cities_degs.csv')
    d = dict()
    for index, row in gpsdf.iterrows():
        d[row['city']] = { 'lat': row['lat'], 'lon': row['lon'] }
    return d
