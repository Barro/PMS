import StringIO
import csv
import datetime
import models
from schedule.models import Location
from party.models import Party
from schedule.models import Event
import string
import re
import unidecode

def extract_date(date):
    return datetime.datetime.strptime(date, "%a %d.%m.%y %H:%M")

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

    for field in ('title_fi', 'title_en', 'location_fi', 'location_en'):
        try:
            field_data[field].decode('UTF-8')
        except UnicodeDecodeError, e:
            errors.append(
                u"Could not decode field '%s' as UTF-8. Make sure that you "
                u"are sending an UTF-8 encoded file." % field)

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


def update_locations(schedule, events):
    existing_locations = {}
    for event in events:
        location_name = event['location_en'].decode('UTF-8')
        location_key = convertNameToKey(location_name)
        if location_key in existing_locations:
            continue
        location = None
        try:
            location = Location.objects.get(key=location_key)
        except Location.DoesNotExist:
            location = models.Location()
            location.key = location_key
            location.name = location_name
            location.url = event.get('location_url', None)
            location.name_fi = event['location_fi']
            location.schedule = schedule
            location.save()
        existing_locations[location_key] = location

    return existing_locations
    
def deleteExtraEvents(newevents):
    print newevents
    eventsToDelete = Event.objects.all()
    for event in eventsToDelete:
        if not event.name in newevents:
        		event.delete()
    return
		
def parse_csv(schedule, data):
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
    fields = ('id', 'outline_number', 'name', 'duration', 'start_date',
              'finish_date', 'asmtv', 'bigscreen', 'major', 'public',
              'sumtask', 'class_', 'url', 'title_en', 'title_fi',
              'location_en', 'location_fi', 'location_url',
              'outline_level', 'description_en', 'description_fi', 'canceled')
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
    locations = update_locations(schedule, rows)
    events = []

    for row in rows:
        if row['public'] != 'Yes':
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
        item_id = None
        try:
            item_id = int(row['id'])
        except ValueError, e:
            messages = [
                (u"Row ID '%s' was not numeric." % row['id'], "warning"),
                (str(row),)
                ]
            raise ScheduleImportError(messages)

        eventname = convertNameToKey(row['title_en'].decode('UTF-8'))
        event = None
        try:
            event = Event.objects.get(name=eventname)
        except Event.DoesNotExist:        
            event = models.Event()
        events.append(eventname)
        event.name = eventname        	  
        categories = ""
        if (row['major'].lower() == 'yes'):
            categories += "major,"
        if (row['asmtv'].lower() == 'yes'):
            categories += "asmtv,"
        if (row['bigscreen'].lower() == 'yes'):
            categories += "bigscreen,"
        if (row['class_'].lower() == 'yes'):
            categories += row['class_'].decode('UTF-8') + ","
        event.categories = categories
        event.time = extract_date(row['start_date'])
        event.end_time = extract_date(row['finish_date'])
        event.original_time = extract_date(row['start_date'])
        event.name_fi = row['title_fi'].decode('UTF-8')
        event.description_fi = row['description_fi'].decode('UTF-8')
        event.description = row['description_en'].decode('UTF-8')
        event.url = row['url']
        event.canceled = (row['canceled'].lower() == 'yes')
        event.schedule = schedule
        location_key = convertNameToKey(row['location_en'].decode('UTF-8'))
        event.location = locations[location_key]
        event.save()
    deleteExtraEvents(events)
		
