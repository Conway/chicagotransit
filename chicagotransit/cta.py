import datetime
import errors
import requests
import xmltodict

_base_url = 'http://www.ctabustracker.com/bustime/api/v1/'

class BusTracker(object):

    def __init__(self, key):
        self.key = key

    def _time_translation(time_str):
        year = int(time_str[0:4])
        month = int(time_str[4:6])
        day = int(time_str[6:8])
        hour = int(time_str[9:11])
        minute = int(time_str[12:14])
        second = int(time_str[15:17])
        time = datetime.datetime(year=year, month=month, day=day, hour=hour, minute=minute, second=second)
        return time

    def time(self):
        url = _base_url + 'gettime'
        result = requests.get(url, params={'key':self.key})
        xml = xmltodict.parse(result.text)
        if 'tm' in xml['bustime-response'].keys():
            time_str = xml['bustime-response']['tm']
            return BusTracker._time_translation(time_str)
        else:
            error = xml['bustime-response']['error']['msg']
            errors.error_handler(error)

    def bus_by_id(self, vid):
        url = _base_url + 'getvehicles'
        result = requests.get(url, params={'key':self.key, 'vid':vid})
        xml = xmltodict.parse(result.text)
        if 'vehicle' in xml['bustime-response'].keys():
            v_data = xml['bustime-response']['vehicle']
            time = v_data['tmstmp']
            latitude = v_data['lat']
            longitude = v_data['lon']
            heading = v_data['hdg']
            pattern_id = v_data['pid']
            route = v_data['rt']
            destination = v_data['des']
            pattern_dist = v_data['pdist']
            speed = v_data['spd']
            bus = BusTracker.Bus(vid, self, time, latitude, longitude, heading, pattern_id, pattern_dist, route, destination, speed)
            return bus
        else:
            error = xml['bustime-response']['error']['msg']
            errors.error_handler(error)

    def routes(self, update=False):
        if hasattr(self, 'bus_routes') and self.bus_routes != [] and update == False:
            return self.bus_routes
        url = _base_url + 'getroutes'
        result = requests.get(url, params={'key':self.key})
        xml = xmltodict.parse(result.text)
        if 'error' in xml['bustime-response'].keys():
            errors.error_handler(xml['bustime-response']['error']['msg'])
        self.bus_routes = []
        for resp in xml['bustime-response']['route']:
            self.bus_routes.append(BusTracker.Route(resp['rt'], self, resp['rtnm']))
        return self.bus_routes

    class Bus(object):
        def __init__(self, id, bt, time, latitude, longitude, heading, pattern_id, pattern_dist, route, destination, speed, delayed=False):
            self.id = id
            self.bt = bt
            self.time = time
            self.latitude = latitude
            self.longitude = longitude
            self.heading = heading
            self.pattern_id = pattern_id
            self.pattern_dist = pattern_dist
            self.route = route
            self.destination = destination
            self.delayed = delayed
            self.speed = speed

        def update(self):
            self = self.bt.bus_by_id(id)

        def __str__(self):
            return "id: {0}, rt {1}".format(self.id, self.route)

    class Route(object):
        def __init__(self, number, bt, description):
            self.number = number
            self.bt = bt
            self.description = description

        def __str__(self):
            return str(self.number)

        def busses(self, update=False):
            url = _base_url + 'getvehicles'
            result = requests.get(url, params={'key':self.bt.key, 'rt':self.number})
            xml = xmltodict.parse(result.text)
            if 'vehicle' in xml['bustime-response'].keys():
                for resp in xml['bustime-response']:
                    vid = resp['vid']
                    time = resp['tmstmp']
                    latitude = resp['lat']
                    longitude = resp['lon']
                    heading = resp['hdg']
                    pattern_id = resp['pid']
                    route = resp['rt']
                    destination = resp['des']
                    pattern_dist = resp['pdist']
                    speed = resp['spd']
                    bus = BusTracker.Bus(vid, self, time, latitude, longitude, heading, pattern_id, pattern_dist, route, destination, speed)
                    self.busses.append(bus)
            else:
                error = xml['bustime-response']['error']['msg']
                errors.error_handler(error)

        def directions(self, update=False):
            if hasattr(self, 'direction') and not update:
                return self.direction
            else:
                self.direction = []
                url = _base_url + 'getdirections'
                result = requests.get(url, params={'key':self.bt.key, 'rt':self.number})
                xml = xmltodict.parse(result.text)
                self.direction = xml['bustime-response']['dir']
                return self.direction

        def stops(self, direction, update=False):
            assert(direction in self.directions())
            url = _base_url + 'getstops'
            result = requests.get(url, params={'key':self.bt.key, 'rt':self.number, 'dir':direction})
            xml = xmltodict.parse(result.text)
            if hasattr(self, 'stop') and not update:
                return self.stops
            elif 'stop' in xml['bustime-response'].keys():
                self.stop = []
                for resp in xml['bustime-response']['stop']:
                    id = resp['stpid']
                    name = resp['stpnm']
                    latitude = resp['lat']
                    longitude = resp['lon']
                    self.stop.append(BusTracker.Stop(id, name, latitude, longitude, self.bt))
                return self.stop
            else:
                error = xml['bustime-response']['error']['msg']
                errors.error_handler(error)

    class Stop(object):
        def __init__(self, id, name, latitude, longitude, bt):
            self.id = id
            self.name = name
            self.latitude = latitude
            self.longitude = longitude
            self.bt = bt