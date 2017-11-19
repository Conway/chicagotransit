import dateutil.parser
import json
import requests
from datetime import datetime
from errors import InvalidKeyException, InvalidLineException


class Metra(object):
    line_abbreviations = ['BNSF', 'HC', 'ME', 'MD-N', 'MD-W', 'NCS',
                          'RI', 'SWS', 'UP-N', 'UP-NW', 'UP-W']
    base_url = "https://gtfsapi.metrarail.com"

    def __init__(self, access_key, secret):
        self.auth = (access_key, secret)
        self.published = None
        # get all stops, and test that API key works
        self.stations()

    def _updated_published(self):
        '''
        Metra publishes the time that the static endpoints were updated at this endpoint
        This method should be called whenever a cached method is called
        '''
        path = "/gtfs/raw/published.txt"
        url = Metra.base_url + path
        result = requests.get(url, auth=self.auth)
        self.published = result.text
        return self.published

    def stations(self, update=False):
        '''
        A static endpoint that gets and stores all of the stations that Metra serves
        '''
        if hasattr(self, 'stops') and self.stops != [] and update is False:
            return self.stops
        self.stops = []
        path = "/gtfs/schedule/stops"
        url = Metra.base_url + path
        result = requests.get(url, auth=self.auth)
        if result.status_code in [401, 403]:
            raise InvalidKeyException()
        for stop in result.json():
            s = Station(stop["stop_id"],
                        stop["stop_name"],
                        stop["stop_lat"],
                        stop["stop_lon"],
                        stop["zone_id"],
                        stop["stop_url"],
                        bool(stop["wheelchair_boarding"]))
            self.stops.append(s)
        self._updated_published()
        return self.stops

    def alerts(self):
        path = "/gtfs/alerts"
        url = Metra.base_url + path
        result = requests.get(url, auth=self.auth)
        if result.status_code in [401, 403]:
            raise InvalidKeyException()
        alerts = []
        for alert in result.json():
            a = Alert(self,
                      alert["id"],
                      alert["alert"]["header_text"]["translation"][0]["text"],
                      alert["alert"]["description_text"]["translation"][0]["text"],
                      alert["alert"]["url"]["translation"][0]["text"],
                      alert["alert"]["active_period"][0]["start"]["low"],
                      alert["alert"]["active_period"][0]["start"]["low"],
                      alert["alert"]["informed_entity"][0]["stop_id"],
                      alert["alert"]["informed_entity"][0]["route_id"])
            alerts.append(a)
        return alerts

    def current_locations(self):
        path = "/gtfs/positions"
        url = Metra.base_url + path
        result = requests.get(url, auth=self.auth)
        if result.status_code in [401, 403]:
            raise InvalidKeyException()
        output = []
        for train in result.json():
            # convert state times to datetime object
            # example: "09:35:0020171025"
            day = train["vehicle"]["trip"]["start_time"]
            hour = train["vehicle"]["trip"]["start_date"]
            start = datetime.strptime(day+hour, "%H:%M:%S%Y%m%d")

            t = Trip(train["id"],
                     train["vehicle"]["trip"]["trip_id"],
                     train["vehicle"]["trip"]["route_id"],
                     start,
                     train["vehicle"]["position"]["latitude"],
                     train["vehicle"]["position"]["longitude"],
                     train["vehicle"]["vehicle"]["id"],
                     train["vehicle"]["vehicle"]["label"],
                     train["vehicle"]["timestamp"]["low"])
            output.append(t)
        return output

class Alert(object):
    def __init__(self, m, id, header, description, url, start, end, stop, line):
        # change start/end times to datetime objects
        try:
            start_time = dateutil.parser.parse(start)
        except ValueError:
            start_time = start

        try:
            end_time = dateutil.parser.parse(end)
        except ValueError:
            end_time = None

        self.m = m
        self.id = id
        self.header = header
        self.description = description
        self.url = url
        self.start = start_time
        self.end = end_time
        if stop:
            # find stop object that correlates with the stop within the alert
            for station in m.stops:
                if station.id.lower() == stop.lower():
                    self.stop = station
                    break
            else:
                self.stop = None
        else:
            self.stop = None
        self.line = line

class Station(object):
    def __init__(self, id, name, lat, lon, zone, url, accessible):
        self.id = id
        self.name = name
        self.lat = lat
        self.lon = lon
        self.zone = zone
        self.url = url
        self.accessible = accessible

class Trip(object):
    def __init__(self, id, trip_id, route, start, lat, lon, vehicle_id, vehicle_label, updated):
        self.id = id
        self.trip_id = trip_id
        self.route = route
        self.start = start #TODO: handle start time? - handling it on clientside
        self.lat = lat
        self.lon = lon
        self.vehicle_id = vehicle_id
        self.vehicle_label = vehicle_label
        # change updated time to datetime objects
        try:
            self.updated = dateutil.parser.parse(updated)
        except ValueError:
            self.updated = updated
