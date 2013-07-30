import StringIO
import csv
import datetime
import dateutil.tz
import models
from schedule.models import Location
from schedule.models import Event
import string
import re
import unidecode


def extract_date(date):
    result = datetime.datetime.strptime(date, "%d.%m.%y %H:%M")
    result.replace(tzinfo=dateutil.tz.tzlocal())
    return result

def get_row_errors(fields, field_data):
    errors = []
    for field in fields:
        if field_data.get(field, None) is None:
            errors.append(u"Field '%s' is missing." % field)

    if len(errors) > 0:
        return errors

    if None in field_data:
        errors.append(
            "There are extra %d field values with event %s (%s)." %
            (len(field_data[None]), field_data['id'].decode("utf-8"),
             field_data['title_en'].decode("utf-8")))
        errors.append(
            u"Make sure that you don't have accidentally pasted text "
            u"with tab characters to descriptions or titles!")

    for field in ('start_date', 'finish_date'):
        try:
            extract_date(field_data[field])
        except ValueError, e:
            errors.append(
                u"Date string on field '%s' is invalid (%s)." % (field, e))
            errors.append(
                u"For example date and time 'Saturday 11th of February 2011 "
                u"18:00' would be 'Sat 12.02.11 18:00'.")

    for field in ('title_fi', 'title_en'):
        try:
            field_data[field].decode('UTF-8')
        except UnicodeDecodeError, e:
            errors.append(
                u"Could not decode field '%s' as UTF-8. Make sure that you "
                u"are sending an UTF-8 encoded file." % field)

    return errors

def get_location_errors(fields, field_data):
    errors = []
    for field in fields:
        if field_data.get(field, None) is None:
            errors.append(u"Field '%s' is missing." % field)

    if len(errors) > 0:
        return errors

    if None in field_data:
        errors.append(
            "There are extra %d field values with event %s (%s)." %
            (len(field_data[None]), field_data['id'].decode("utf-8"),
             field_data['title_en'].decode("utf-8")))
        errors.append(
            u"Make sure that you don't have accidentally pasted text "
            u"with tab characters to descriptions or titles!")

#    for field in ('Location_ID', 'Location_EN', 'Location_FI', 'Location_URL', 'Description_EN', 'Description_FI'):
#        try:
#            field_data[field].decode('UTF-8')
#        except UnicodeDecodeError, e:
#            errors.append(
#                u"Could not decode field '%s' as UTF-8. Make sure that you "
#                u"are sending an UTF-8 encoded file." % field)

    return errors

class InvalidParserError(RuntimeError):
    pass


class ScheduleImportError(RuntimeError):
    def __init__(self, messages):
        self.messages = messages

KEY_CHARACTERS = (string.ascii_letters.decode('ascii')
                  + string.digits.decode('ascii'))
NORMALIZE_REGEX = re.compile(ur'([^%s]+)' % KEY_CHARACTERS)


def convertNameToKey(name):
    ascii_normalized = unidecode.unidecode(name)
    special_character_normalized = NORMALIZE_REGEX.sub(
        ur'-', ascii_normalized.lower())
    return special_character_normalized.strip("-")


def parse_events(data):
    sniff_data = data[:50]
    if ";" not in sniff_data and "\t" not in sniff_data:
        raise InvalidParserError()
    try:
        dialect = csv.Sniffer().sniff(data)
    except csv.Error, e:
        messages = [
            (u"%s." % e.message, "warning"),
            (u"Make sure that all lines contain the same number of field "
             u"delimiter characters.",),
            (u"First row of data: %s" % data.split("\n")[0],),
            ]
        raise ScheduleImportError(messages)

    data = StringIO.StringIO(data)
    fields = "id;name;duration;start_date;finish_date;asmtv;bigscreen;major;public;onsite;sumtask;category;subcategory;url;title_en;title_fi;location_id;canceled".split(";")
    reader = csv.DictReader(data, fieldnames=fields, dialect=dialect)
    reader = iter(reader)

    # Grab all the public events so that the raw data can be shown.
    public_data = StringIO.StringIO()
    writer = csv.DictWriter(
        public_data,
        fieldnames=fields,
        dialect=dialect,
        quotechar="\\")

    # Ignore the first row
    header = reader.next()
    try:
        writer.writerow(header)
    except (ValueError, TypeError), e:
        # This error comes only when there are too many fields in data.
        field_count = reduce(
            lambda x, y: type(y) == list and x + len(y) or x + 1,
            header.values(),
            0)
        messages = [(u"Data contains %d fields when expecting %d." %
                    (field_count, len(fields)), "warning")]
        raise ScheduleImportError(messages)

    rows = list(reader)
    events = []

    for row in rows:
        if row['public'].lower() != 'yes':
            continue
        errors = get_row_errors(fields, row)
        if len(errors) > 0:
            messages = [
                (u"Schedule data has an invalid row", "warning")
                ]
            for error in errors:
                messages.append((error, "warning"))
                messages.append((row, "warning"))
            raise ScheduleImportError(messages)
        try:
            writer.writerow(row)
        except (ValueError, TypeError), e:
            messages = [
                (u"Unexpected error happened (ValueError): %s" %
                    e.message, "warning"),
                (str(row),)]
            raise ScheduleImportError(messages)
        except csv.Error, e:
            messages = [
                (u"Unexpected error happened (csv.Error): %s" %
                    e.message, "warning"),
                (str(row),)
                ]
            raise ScheduleImportError(messages)
        except TypeError, e:
            messages = [
                (u"Unexpected error happened (TypeError): %s" %
                    e.message, "warning"),
                (str(row),)
                ]
            raise ScheduleImportError(messages)

        event = parse_event(row)
        events.append(event)

    return events


def parse_location_csv(data):
    print "Parsing location data"
    sniff_data = data[:50]
    if ";" not in sniff_data and "\t" not in sniff_data:
        raise InvalidParserError()
    try:
        dialect = csv.Sniffer().sniff(data)
    except csv.Error, e:
        messages = [
            (u"%s." % e.message, "warning"),
            (u"Make sure that all lines contain the same number of field "
             u"delimiter characters.",),
            (u"First row of data: %s" % data.split("\n")[0],),
            ]
        raise ScheduleImportError(messages)

    data = StringIO.StringIO(data)
    fields = ('Location_ID', 'Location_EN', 'Location_FI', 'Location_URL', 'Description_EN', 'Description_FI')
    reader = csv.DictReader(data, fieldnames=fields, dialect=dialect)
    reader = iter(reader)

    # Grab all the public events so that the raw data can be shown.
    public_data = StringIO.StringIO()
    writer = csv.DictWriter(
        public_data,
        fieldnames=fields,
        dialect=dialect,
        quotechar="\\")

    # Ignore the first row
    header = reader.next()
    try:
        writer.writerow(header)
    except (ValueError, TypeError), e:
        # This error comes only when there are too many fields in data.
        field_count = reduce(
            lambda x, y: type(y) == list and x + len(y) or x + 1,
            header.values(),
            0)
        messages = [(u"Data contains %d fields when expecting %d." %
                    (field_count, len(fields)), "warning")]
        raise ScheduleImportError(messages)

    rows = list(reader)
    locations = []

    for row in rows:
        errors = get_location_errors(fields, row)
        if len(errors) > 0:
            messages = [
                (u"Schedule data has an invalid row", "warning")
                ]
            for error in errors:
                messages.append((error, "warning"))
                messages.append((row, "warning"))
            raise ScheduleImportError(messages)
        try:
            writer.writerow(row)
        except (ValueError, TypeError), e:
            messages = [
                (u"Unexpected error happened (ValueError): %s" %
                    e.message, "warning"),
                (str(row),)]
            raise ScheduleImportError(messages)
        except csv.Error, e:
            messages = [
                (u"Unexpected error happened (csv.Error): %s" %
                    e.message, "warning"),
                (str(row),)
                ]
            raise ScheduleImportError(messages)
        except TypeError, e:
            messages = [
                (u"Unexpected error happened (TypeError): %s" %
                    e.message, "warning"),
                (str(row),)
                ]
            raise ScheduleImportError(messages)

        location = locationparser(row)
        locations.append(location)

    return locations


def locationparser(row):
    location = {}
    location['key'] = row['Location_ID'].decode('UTF-8')
    location['name'] = row['Location_EN']
    location['name_fi'] = row['Location_FI']
    location['description'] = row['Description_EN']
    location['description_fi'] = row['Description_FI']
    url = row.get('Location_URL', "")
    if len(url) and url.startswith("/"):
        url = "http://www.assembly.org%s" % url
    location['url'] = url
    return location


def parse_event(row):
    try:
        event_id = int(row['id'])
    except ValueError:
        messages = [
            (u"Row ID '%s' was not numeric." % row['id'], "warning"),
            (str(row),)
            ]
        raise ScheduleImportError(messages)
    event = {'key': event_id}
    event['location_key'] = row['location_id']
    event['name'] = row['title_en'].decode('UTF-8')
    event['name_fi'] = row['title_fi'].decode('UTF-8')
    flags = []
    if (row['major'].lower() == 'yes'):
        flags.append("major")
    if (row['asmtv'].lower() == 'yes'):
        flags.append("asmtv")
    if (row['bigscreen'].lower() == 'yes'):
        flags.append("bigscreen")
    if (row['onsite'].lower() == 'yes'):
        flags.append("onsite")
    event['flags'] = ",".join(flags)
    event['start_time'] = extract_date(row['start_date'])
    event['end_time'] = extract_date(row['finish_date'])
    event['original_time'] = extract_date(row['start_date'])
    categories = [row['category'].decode('UTF-8')]
    if row['subcategory']:
        categories.append(row['subcategory'].decode('UTF-8'))
    event["categories"] = ",".join(categories)
    url = row['url']
    if len(url) and url.startswith("/"):
        url = "http://www.assembly.org%s" % url
    event['url'] = url
    event['canceled'] = (row['canceled'].lower() == 'yes')
    return event


def parse_location(row):
    location_name = row['location_en'].decode('UTF-8')
    location = {}
    location['key'] = convertNameToKey(location_name)
    location['name'] = location_name
    location['name_fi'] = row['title_fi']
    url = row.get('location_url', "")
    if len(url) and url.startswith("/"):
        url = "http://www.assembly.org%s" % url
    location['url'] = url
    return location


def delete_unknown_locations(schedule, all_locations, known_locations):
    for location in all_locations:
        if not location.key in known_locations:
            location.delete()


def delete_unknown_events(schedule, all_events, known_events):
    for event in all_events:
        if not event.key in known_events:
            event.delete()


def update_schedule_database(schedule, locations, events):
    all_locations = Location.objects.filter(schedule=schedule)
    keyed_locations = {}
    for location in all_locations:
        keyed_locations[location.key] = location
    if locations is not None:
        delete_unknown_locations(schedule, all_locations, locations)
    else:
        locations = []
    if events is not None:
        all_events = Event.objects.filter(schedule=schedule)
        event_keys = set([event['key'] for event in events])
        delete_unknown_events(schedule, all_events, event_keys)
    else:
        events = []
    for location in locations:
        try:
            location_obj = Location.objects.get(
                schedule=schedule, key=location['key'])
        except Location.DoesNotExist:
            location_obj = models.Location()
        location_obj.key = location['key']
        location_obj.schedule = schedule
        location_obj.name = location['name']
        location_obj.description = location['description']
        location_obj.description_fi = location['description_fi']
        location_obj.name_fi = location['name_fi']
        location_obj.url = location['url']
        location_obj.save()
        keyed_locations[location_obj.key] = location_obj

    if events is not None:
        for event in events:
            try:
                event_obj = Event.objects.get(schedule=schedule, key=event['key'])
            except Event.DoesNotExist:
                event_obj = models.Event()
            event_obj.schedule = schedule
            if event['location_key']:
                event_obj.location = keyed_locations[event['location_key']]
            event_obj.key = event['key']
            event_obj.name = event['name']
            event_obj.name_fi = event['name_fi']
            event_obj.time = event['start_time']
            event_obj.end_time = event['end_time']
            event_obj.original_time = event['original_time']
            event_obj.url = event['url']
            event_obj.flags = event['flags']
            event_obj.categories = event['categories']
            event_obj.canceled = event['canceled']
            event_obj.save()
