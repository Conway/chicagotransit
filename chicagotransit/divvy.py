import datetime
import json
import requests

_url = 'https://www.divvybikes.com/stations/json'
class Divvy(object):
    def __init__(self):
        self.stations = []
        self.update()

    def update(self):
        resp = json.loads(requests.get(_url).text)
        self.stations = []
        for station in resp['stationBeanList']:
            id = int(station['id'])
            name = station['stationName']
            available = int(station['availableDocks'])
            total = int(station['totalDocks'])
            latitude = int(station['latitude'])
            longitude = int(station['longitude'])
            status_value = station['statusValue']
            status_key = int(station['statusKey'])
            if station['is_renting'].lower() == 'true':
                renting = True
            else:
                renting = False
            date_str = str(station['lastCommunicationTime'])
            month = int(date_str[0:2])
            day = int(date_str[3:5])
            year = int(date_str[6:10])
            if date_str[len(date_str)-1].lower() == 'p':
                hour = int(date_str[11:13]) + 12
            else:
                hour = int(date_str[11:13])
            minute = int(date_str[14:16])
            second = int(date_str[17:19])
            updated = datetime.datetime(year=year, month=month, day=day, hour=hour, minute=minute, second=second)
            s = Station(id, name, available, total, latitude, longitude, status_value, status_key, renting, updated)
            self.stations.append(s)

    def by_id(self, id):
        for station in self.stations:
            if station.id == id:
                return station

class Station(object):
    def __init__(self, id, name, available, total, latitude, longitude, status_value, status_key, renting, updated):
        self.id = id
        self.name = name
        self.available = available
        self.total = total
        self.latitude = latitude
        self.longitude = longitude
        self.status_value = status_value
        self.status_key = status_key
        self.renting = renting
        self.updated = updated