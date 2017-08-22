import datetime
import difflib
from django.db.models import Min, Q, Prefetch
from django.utils.text import slugify
from multigtfs.models import Feed, Trip, StopTime
from .ni import Grouping, Timetable, Row


def get_grouping_name_part(stop_name):
    parts = stop_name.split(', ')
    if len(parts) == 2:
        if slugify(parts[1]).startswith(slugify(parts[0])):
            return parts[1]
        if slugify(parts[1]) in slugify(parts[0]):
            return parts[0]
    return stop_name


def get_grouping_name(grouping):
    return '{} - {}'.format(get_grouping_name_part(grouping.rows[0].part.stop.name),
                            get_grouping_name_part(grouping.rows[-1].part.stop.name))


def handle_trips(trips, day):
    i = 0
    head = None

    if not day:
        day = datetime.date.today()
    midnight = datetime.datetime.combine(day, datetime.time())

    previous_list = []

    for trip in trips:
        previous = None

        current_list = [stop.stop.stop_id for stop in trip.stoptime_set.all()]
        diff = difflib.ndiff(previous_list, current_list)

        for stop in trip.stoptime_set.all():
            stop_id = stop.stop.stop_id
            instructions = next(diff)

            while instructions[0] in '-?':
                instructions = next(diff)

            if instructions == '+ ' + stop_id:
                row = Row(stop_id, ['     '] * i)
                row.part.stop.name = stop.stop.name
                if previous:
                    previous.append(row)
                else:
                    if head:
                        head.prepend(row)
                    head = row
            else:
                row = previous or head
                while row.part.stop.atco_code != stop_id:
                    row = row.next

            time = datetime.timedelta(seconds=(stop.departure_time or stop.arrival_time).seconds)
            time = (midnight + time).time()
            row.times.append(time)
            row.part.timingstatus = None
            previous = row

        previous_list = head.list()

        if i:
            p = head
            while p:
                if len(p.times) == i:
                    p.times.append('     ')
                p = p.next
        i += 1
    p = head
    g = Grouping()

    while p:
        g.rows.append(p)
        p = p.next
    return g


def get_timetable(routes, day=None, collection=None):
    if not routes:
        return

    trips_dict = {}

    trips = Trip.objects.filter(route__in=routes).defer('geometry')
    trips = trips.annotate(departure_time=Min('stoptime__departure_time')).order_by('departure_time')
    if day:
        trips = trips.filter(Q(service__servicedate__date=day, service__servicedate__exception_type=1) |
                             Q(service__start_date__lte=day, service__end_date__gte=day,
                               **{'service__' + day.strftime('%A').lower(): True}))
        trips = trips.exclude(service__servicedate__date=day, service__servicedate__exception_type=2)
    prefetch = Prefetch('stoptime_set', queryset=StopTime.objects.select_related('stop').order_by('stop_sequence'))
    trips = trips.prefetch_related(prefetch).select_related('service')
    for trip in trips:
        direction = trip.direction
        if direction == '':
            direction = trip.shape_id
        if direction in trips_dict:
            trips_dict[direction].append(trip)
        else:
            trips_dict[direction] = [trip]

    t = Timetable()
    t.groupings = [handle_trips(trips_dict[key], day) for key in trips_dict]
    t.date = day
    for grouping in t.groupings:
        grouping.name = get_grouping_name(grouping)
        for row in grouping.rows:
            if collection in {'ouibus', 'metz', 'nancy'}:
                row.part.stop.atco_code = collection + '-' + row.part.stop.atco_code
            elif collection == 'flixbus':
                row.part.stop.atco_code = collection + '-' + row.part.stop.atco_code[8:]
    return t


def get_timetables(service_code, day):
    parts = service_code.split('-', 1)
    collection = parts[0]
    route_id = parts[1]

    if len(collection) == 10:
        feed = Feed.objects.filter(name__startswith=collection)
    else:
        feed = Feed.objects.filter(name=collection)
    try:
        feed = feed.latest('created')
    except Feed.DoesNotExist:
        return

    if collection == 'flixbus':
        routes = feed.route_set.filter(route_id=collection.upper() + ':' + route_id)
    elif collection in {'ouibus', 'metz', 'nancy'}:
        routes = feed.route_set.filter(route_id=route_id)
    else:  # Ireland
        route_id += '-'
        routes = feed.route_set.filter(route_id__startswith=route_id)

    timetable = get_timetable(routes, day=day, collection=collection)

    if timetable:
        return [timetable]
