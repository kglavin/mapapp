
import pandas as pd

def gendict():
    gpsdf = pd.read_csv('cities_degs.csv')
    d = dict()
    for index, row in gpsdf.iterrows():
        s = row['city']
        s.replace(" ","_")
        d[s] = { 'lat': row['lat'], 'lon': row['lon'] }
    return d
