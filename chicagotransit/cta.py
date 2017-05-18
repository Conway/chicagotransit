import datetime
import errors
import requests
import xmltodict

_base_url = 'http://www.ctabustracker.com/bustime/api/v1/'
_base_train = 'http://lapi.transitchicago.com/api/1.0/'

def _time_translation(time_str):
        year = int(time_str[0:4])
        month = int(time_str[4:6])
        day = int(time_str[6:8])
        hour = int(time_str[9:11])
        minute = int(time_str[12:14])
        second = int(time_str[15:17])
        time = datetime.datetime(
            year=year,
            month=month,
            day=day,
            hour=hour,
            minute=minute,
            second=second)
        return time

class BusTracker(object):

    def __init__(self, key):
        self.key = key

    def time(self):
        url = _base_url + 'gettime'
        result = requests.get(url, params={'key': self.key})
        xml = xmltodict.parse(result.text)
        if 'tm' in list(xml['bustime-response'].keys()):
            time_str = xml['bustime-response']['tm']
            return _time_translation(time_str)
        else:
            error = xml['bustime-response']['error']['msg']
            errors.error_handler(error)

    def bus_by_id(self, vid):
        url = _base_url + 'getvehicles'
        result = requests.get(url, params={'key': self.key, 'vid': vid})
        xml = xmltodict.parse(result.text)
        if 'vehicle' in list(xml['bustime-response'].keys()):
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
            bus = BusTracker.Bus(vid, self, time, latitude, longitude, heading,
                                 pattern_id, pattern_dist, route, destination,
                                 speed)
            return bus
        else:
            error = xml['bustime-response']['error']['msg']
            errors.error_handler(error)

    def routes(self, update=False):
        if (
            hasattr(self, 'bus_routes') and
            self.bus_routes != [] and
            update is False
        ):
            return self.bus_routes
        url = _base_url + 'getroutes'
        result = requests.get(url, params={'key': self.key})
        xml = xmltodict.parse(result.text)
        if 'error' in list(xml['bustime-response'].keys()):
            errors.error_handler(xml['bustime-response']['error']['msg'])
        self.bus_routes = []
        for resp in xml['bustime-response']['route']:
            rt = BusTracker.Route(resp['rt'], self, resp['rtnm'])
            self.bus_routes.append(rt)
        return self.bus_routes

    class Bus(object):
        def __init__(self, id, bt, time, latitude, longitude, heading,
                     pattern_id, pattern_dist, route, destination, speed,
                     delayed=False):
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
            params = {'key': self.bt.key, 'rt': self.number}
            result = requests.get(url, params=params)
            xml = xmltodict.parse(result.text)
            if 'vehicle' in list(xml['bustime-response'].keys()):
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
                    bus = BusTracker.Bus(vid, self, time, latitude, longitude,
                                         heading, pattern_id, pattern_dist,
                                         route, destination, speed)
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
                params = {'key': self.bt.key, 'rt': self.number}
                result = requests.get(url, params=params)
                xml = xmltodict.parse(result.text)
                self.direction = xml['bustime-response']['dir']
                return self.direction

        def stops(self, direction, update=False):
            assert(direction in self.directions())
            url = _base_url + 'getstops'
            params = {'key': self.bt.key, 'rt': self.number, 'dir': direction}
            result = requests.get(url, params=params)
            xml = xmltodict.parse(result.text)
            if hasattr(self, 'stop') and not update:
                return self.stops
            elif 'stop' in list(xml['bustime-response'].keys()):
                self.stop = []
                for resp in xml['bustime-response']['stop']:
                    id = resp['stpid']
                    name = resp['stpnm']
                    latitude = resp['lat']
                    longitude = resp['lon']
                    stop = BusTracker.Stop(id, name, latitude,
                                           longitude, self.bt)
                    self.stop.append(stop)
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

class TrainTracker(object):

    def __init__(self, key):
        self.key = key

    def arrival_time_by_station(self, staid, max=None, route=None):
        params = {'key':self.key, 'mapid':staid}
        if max:
            params['max'] = max
        if route:
            params['rt'] = route
        url = _base_train + 'ttarrivals.aspx'
        response = requests.get(url, params=params)
        xml = xmltodict.parse(response.text)['ctatt']
        if xml['errNm']:
            raise ValueError(xml['errNm'])
        out = []
        t = _time_translation(xml['tmst'])
        for arrival in xml['eta']:
            arr = TrainTracker.Stop(self,
                                    arrival['staId'],
                                    arrival['stpId'],
                                    arrival['staNm'],
                                    arrival['stpDe'],
                                    arrival['rn'],
                                    arrival['rt'],
                                    arrival['destSt'],
                                    arrival['destNm'],
                                    arrival['trDr'],
                                    t,
                                    _time_translation(arrival['prdt']),
                                    _time_translation(arrival['arrT']),
                                    bool(arrival['isApp']),
                                    bool(arrival['isSch']),
                                    bool(arrival['isDly']),
                                    bool(arrival['isFlt']),
                                    arrival['lat'],
                                    arrival['lon'],
                                    arrival['heading'])
            out.append(arr)
        return out

    def arrival_time_by_stop(self, stpid, max=None, route=None):
        params = {'key':self.key, 'stpid':stpid}
        if max:
            params['max'] = max
        if route:
            params['rt'] = route
        url = _base_train + 'ttarrivals.aspx'
        response = requests.get(url, params=params)
        xml = xmltodict.parse(response.text)['ctatt']
        if xml['errNm']:
            raise ValueError(xml['errNm'])
        out = []
        t = _time_translation(xml['tmst'])
        for arrival in xml['eta']:
            arr = TrainTracker.Stop(self,
                                    arrival['staId'],
                                    arrival['stpId'],
                                    arrival['staNm'],
                                    arrival['stpDe'],
                                    arrival['rn'],
                                    arrival['rt'],
                                    arrival['destSt'],
                                    arrival['destNm'],
                                    arrival['trDr'],
                                    t,
                                    _time_translation(arrival['prdt']),
                                    _time_translation(arrival['arrT']),
                                    bool(arrival['isApp']),
                                    bool(arrival['isSch']),
                                    bool(arrival['isDly']),
                                    bool(arrival['isFlt']),
                                    arrival['lat'],
                                    arrival['lon'],
                                    arrival['heading'])
            out.append(arr)
        return out

    def train_positions(self, line):
        routes = ['red', 'blue', 'brn', 'g', 'org', 'p', 'pink', 'y']
        if line not in routes:
            raise ValueError('Invalid Line')
        url = _base_train + "ttpositions.aspx"
        response = requests.get(url, params={'key': self.key, 'rt': line})
        xml = xmltodict.parse(response.text)['ctatt']
        if xml['errNm']:
            raise ValueError(xml['errNm'])
        trains = []
        for train in xml['route']['train']:
            t = TrainTracker.Train(
                self,
                train['rn'],
                train['destSt'],
                train['destNm'],
                train['trDr'],
                train['nextStaId'],
                train['nextStpId'],
                train['nextStaNm'],
                _time_translation(train['prdt']),
                bool(train['isApp']),
                bool(train['isDly']),
                train['lat'],
                train['lon'],
                train['heading'],
                line)
            trains.append(t)
        return trains


    class Stop(object):
        def __init__(self, tt, station_id, stop_id, station_name, station_desc,
                     run, route, dest_station, dest_name, train_dir, gen_time,
                     pre_gen_time, arr_time, is_approaching, is_scheduled,
                     has_fault, is_delayed, lat, lon, heading):
            self.tt = tt
            self.station_id = station_id
            self.stop_id = stop_id
            self.station_name = station_name
            self.station_description = station_desc
            self.run = run
            self.route = route
            self.destination_station = dest_station
            self.destination_name = dest_name
            self.train_direction = train_dir
            self.gen_time = gen_time
            self.prediction_time = pre_gen_time
            self.arrival_time = arr_time
            self.is_approaching = is_approaching
            self.is_scheduled = is_scheduled
            self.is_live = not is_scheduled
            self.has_fault = has_fault
            self.is_delayed = is_delayed
            self.lat = lat
            self.lon = lon
            self.heading = heading

    class Train(object):

        def __init__(self, tt, run, destination_num, destination_name, train_dir,
                     next_station_id, next_stop_id, next_station_name,
                     prediction_time, is_approaching, is_delayed, lat, lon,
                     heading, line):
            self.tt = tt
            self.run = run
            self.destination_num = destination_num
            self.destionation_name = destination_name
            self.train_dir = train_dir
            self.next_station_id = next_station_id
            self.next_stop_id = next_stop_id
            self.next_station_name = next_station_name
            self.prediction_time = prediction_time
            self.is_approaching = is_approaching
            self.is_delayed = is_delayed
            self.lat = lat
            self.lon = lon
            self.heading = heading
            self.line = line

        def __str__(self):
            return str(self.line) + ":" + str(self.run)

        def follow(self):
            params = {'key':self.tt.key, 'runnumber':self.run}
            url = _base_train + 'ttfollow.aspx'
            response = requests.get(url, params=params)
            xml = xmltodict.parse(response.text)['ctatt']
            if xml['errNm']:
                raise ValueError(xml['errNm'])
            lat = xml['position']['lat']
            lon = xml['position']['lon']
            heading = xml['position']['heading']
            t = _time_translation(xml['tmst'])
            arrivals = []
            for arrival in xml['eta']:
                stop = TrainTracker.Stop(self.tt, arrival['staId'],
                                         arrival['stpId'], arrival['staNm'],
                                         arrival['stpDe'], arrival['rn'],
                                         arrival['rt'], arrival['destSt'],
                                         arrival['destNm'], arrival['trDr'], t,
                                         _time_translation(arrival['prdt']),
                                         _time_translation(arrival['arrT']),
                                         bool(arrival['isApp']),
                                         bool(arrival['isSch']),
                                         bool(arrival['isFlt']),
                                         bool(arrival['isDly']), lat, lon,
                                         heading)
                arrivals.append(stop)
            return arrivals

