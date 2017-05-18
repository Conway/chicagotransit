import json
import requests
from errors import InvalidLineException


def line_error_handler(line):
    # TODO: make this a decorator (maybe?)
    if line.upper() not in MetraTrainTracker.line_abbreviations:
            raise InvalidLineException("{0} is not a valid line".format(line))


class MetraTrainTracker(object):
    line_abbreviations = ['BNSF', 'HC', 'ME', 'MD-N', 'MD-W', 'NCS',
                          'RI', 'SWS', 'UP-N', 'UP-NW', 'UP-W']

    @staticmethod
    def stations(line):
        line_error_handler(line)
        url = "http://metrarail.com/content/metra/en/home/jcr:content/trainTracker.get_stations_from_line.json"  # noqa
        data = {"trainLineId": line.upper(), "trackerNumber": 0}
        # trackerNumber appears to be a required param that does nothing
        req = requests.get(url, params=data)
        j = json.loads(req.text)
        stations = []
        for s_order in list(j['stations'].keys()):
            name = j['stations'][s_order]['name']
            id = j['stations'][s_order]['id']
            stations.append(Station(id, name))
        return stations

    @staticmethod
    def trains(line, origin, destination):
        line_error_handler(line)
        url = "http://metrarail.com/content/metra/en/home/jcr:content/trainTracker.get_train_data.json"  # noqa
        data = {'line': line, 'origin': origin, 'destination': destination}
        req = requests.get(url, params=data)
        j = json.loads(req.text)
        trains = []
        for key in list(j.keys()):
            if key[0:5].lower() == 'train':
                t_dict = j[key]
                train_num = t_dict['train_num']
                trip_id = t_dict['trip_id']
                departure_time = t_dict['scheduled_dpt_time']
                departure_time_period = t_dict['schDepartInTheAM']
                arrival_time = t_dict['scheduled_arv_time']
                arrival_time_period = t_dict['schArriveInTheAM']
                departed = t_dict['notDeparted']
                if t_dict['bikesText'].lower() == 'yes':
                    bikes_allowed = True
                else:
                    bikes_allowed = False
                timestamp = t_dict['timestamp']
                trip = Trip(train_num, trip_id, departure_time,
                            departure_time_period, arrival_time,
                            arrival_time_period, departed, bikes_allowed,
                            timestamp)
                trains.append(trip)
        start_name = j['departureStopName']
        end_name = j['arrivalStopName']
        route = Route(origin, start_name, destination, end_name, trains)
        return route


class Station(object):
    def __init__(self, id, name):
        self.id = id
        self.name = name


class Route(object):
    def __init__(self, start_id, start_name, dest_id, dest_name, trains):
        self.start = Station(start_id, start_name)
        self.destination = Station(dest_id, dest_name)
        self.trains = trains


class Trip(object):
    def __init__(self, train_num, trip_id, departure_time,
                 departure_time_period, arrival_time, arrival_time_period,
                 departed, bikes_allowed, timestamp):
        self.train_num = train_num
        self.trip_id = trip_id
        self.departure_time = departure_time
        self.departure_time_period = departure_time_period
        self.arrival_time = arrival_time
        self.arrival_time_period = arrival_time_period
        self.departed = departed
        self.bikes_allowed = bikes_allowed
        self.timestamp = timestamp
