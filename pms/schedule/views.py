# Create your views here.

from django import forms
from django.core import serializers
from django.db import transaction
from django.db.models import Q
from django.shortcuts import render_to_response
from django.http import HttpResponse, HttpResponseNotFound
from django.template import RequestContext
from django.contrib.auth.decorators import permission_required
from datetime import datetime, timedelta
import dateutil.tz
import importcsv
import json
from party.decorators import require_party
from pms.party.models import Party
import re
from schedule.models import Schedule, Event, \
    EventForm, Location, LocationForm, EventHistory
import string


@require_party
def schedule(request, futureonly=True):
    """simple view. futureonly=True shows only things that are in the future
    or don't have an end time and started less than 5 minutes ago."""
    party = Party.objects.get(slug=request.party)
    try:
        schedule = Schedule.objects.get(party=party)
    except Schedule.DoesNotExist:
        return {}
    if futureonly:
        #filter things that have ended less than 5 minutes ago
        #or if they don't have an end, that have started less than 5 minutes
        #ago
        events = Event.objects.filter(Q(schedule=schedule),
                    (
                    Q(end_time__gt=(datetime.now()-timedelta(minutes=5))) |
                    (
                        Q(end_time=None) &
                        Q(time__gt=(datetime.now()-timedelta(minutes=5)))
                    )
                    )
                )
    else:
        events = Event.objects.filter(schedule=schedule).order_by("time")
    return render_to_response('schedule_index.html',
                            {'party':party,'events':events}
                            ,context_instance=RequestContext(request))

@require_party
@permission_required('schedule.admin')
def admin(request, event, success=False, status=None):
    """
    Basic handling of event objects-
    """
    try:
        event = Event.objects.get(pk=event)
    except Event.DoesNotExist:
        return HttpResponseNotFound
    if request.method == 'POST' and not success:
        form = EventForm(request.POST,instance=event)
        if form.is_valid():
            form.save()
            success=True
            status='Event updated'
    else:
        form = EventForm(instance=event)

    return render_to_response("events_adminform.html",{'form':form,'success':success,'event' :event, 'status':status},context_instance=RequestContext(request))

from django import forms

class UploadFileForm(forms.Form):
    from django.core.files.uploadedfile import SimpleUploadedFile
    eventfile  = forms.FileField(required=False)
    locationfile = forms.FileField(required=False)


@require_party
@transaction.commit_on_success
@permission_required('schedule.admin')
def importschedule(request):
    success = False
    if request.method == 'POST':
        form = UploadFileForm(request.POST, request.FILES)
        if form.is_valid():
            party = Party.objects.get(slug=request.party)
            schedule = Schedule.objects.get(party=party)
            if 'locationfile' in form.files:
                csv_location_data = form.files['locationfile'].read()
                csv_location_data = re.sub("[\r\n]+", "\n", csv_location_data)
                locations = importcsv.parse_location_csv(csv_location_data)
                importcsv.update_schedule_database(schedule, locations, None)
            if 'eventfile' in form.files:
                csv_event_data = form.files['eventfile'].read()
                csv_event_data = re.sub("[\r\n]+", "\n", csv_event_data)
                events = importcsv.parse_events(csv_event_data)
                importcsv.update_schedule_database(schedule, None, events)
            return render_to_response(
                "import_success.html",
                context_instance=RequestContext(request))
    else:
        form = UploadFileForm()
    return render_to_response(
        "events_importform.html",
        {'form1': form, 'form2': form, 'success': success},
        context_instance=RequestContext(request))


@require_party
@permission_required('schedule.admin')
def create(request):
    success = False
    try:
        if request.method == 'POST':
            form = EventForm(request.POST)
            if form.is_valid():
                try:
#                    party = Party.objects.get(slug=request.party)
#                    schedule = Schedule.objects.get(party=party)
                    event = form.save(commit=False)
#                    import pdb
#                    pdb.set_trace()
                    event.original_time = event.time
                    party = Party.objects.get(slug=request.party)
                    event.save()
                   # schedule.events.add(event)
                except Exception as e:
                    print e
                success = True
                return admin(request, event.pk, True, 'Event created',
                party=request.party)
        else:
            form = EventForm()

        return render_to_response(
            "events_createform.html",
            {'form': form,
             'success': success},
            context_instance=RequestContext(request))
    except Exception as e:
        pass
    party = Party.objects.get(slug=party)
    return render_to_response('schedule_index.html', {'party':party},context_instance=RequestContext(request))


@require_party
@permission_required('schedule.admin')
def delete(request, event=0):
    try:
        event = Event.objects.get(id=event)
    except Event.DoesNotExist:
        return HttpResponseNotFound()

    event.delete()
    return HttpResponse("Event has been terminated with extreme prejudice.")


@require_party
@permission_required('schedule.admin')
def changelog(request):
    """
    Show changes from EventHistory. This is going to be a huge list.
    Worry about pagination later.
    """
    try:
        party = Party.objects.get(slug=request.party)
        schedule = Schedule.objects.get(party=party)
    except Party.DoesNotExist:
        return HttpResponseNotFound()
    except Schedule.DoesNotExist:
        return HttpResponseNotFound()

    histories = EventHistory.objects.filter(schedule=schedule).order_by('-time')

    return render_to_response(
        "schedule_changelog.html",
        {'histories': histories},
        context_instance=RequestContext(request)
        )


@require_party
@permission_required('schedule.admin')
def createlocation(request):
    success = False
    if request.method != 'POST':
        form = LocationForm()
        return render_to_response(
            "locations_createform.html", {
                'form':form,
                'success':success
                },
            context_instance=RequestContext(request)
            )

    form = LocationForm(request.POST)
    if not form.is_valid():
        return render_to_response(
            "locations_createform.html", {
                'form':form,
                'success':success
                },
            context_instance=RequestContext(request)
            )

    try:
        location = form.save(commit=False)
        location.save()
    except Exception as e:
        print e
        return
    success = True
    return admin(request, location.pk, True, 'Location created', party=request.party)


def encode_export_date(datetimeobj, tzlocal):
    return datetimeobj.replace(tzinfo=tzlocal).strftime("%Y-%m-%dT%H:%M%z")


def dict_add_if_value_nonzero(dictionary, key, value):
    if value:
        dictionary[key] = value


def clean_json_dictionary_value(dictionary, key):
    if key not in dictionary:
        return
    if not dictionary[key]:
        return
    dictionary[key] = dictionary[key].replace("\r", "")
    dictionary[key] = dictionary[key].strip()


@require_party
def eventsjson(request):
    """Shows all non-hidden events in .JSON format."""

    party = Party.objects.get(slug=request.party)
    try:
        schedule = Schedule.objects.get(party=party)
    except Schedule.DoesNotExist:
        return {}

    result = {}

    tzlocal = dateutil.tz.tzlocal()
    location_objects = Location.objects.filter(schedule=schedule)
    locations = {}
    for location in location_objects:
        location_data = {'name': location.name}
        dict_add_if_value_nonzero(location_data, 'name_fi', location.name_fi)
        dict_add_if_value_nonzero(location_data, 'url', location.url)
        dict_add_if_value_nonzero(
            location_data, 'description', location.description)
        dict_add_if_value_nonzero(
            location_data, 'description_fi', location.description_fi)
        locations[location.key] = location_data
    result['locations'] = locations

    events = []
    event_objects = Event.objects.filter(
        schedule=schedule, hidden=False).order_by("time", "order")
    for event in event_objects:
        event_key = "%s-%s" % (party.slug, event.key)
        event_data = {
            'key': event_key,
            'name': event.name,
            'start_time': encode_export_date(event.time, tzlocal)
            }
        dict_add_if_value_nonzero(event_data, 'name_fi', event.name_fi)
        dict_add_if_value_nonzero(
            event_data,
            'original_start_time',
            encode_export_date(event.original_time, tzlocal))
        dict_add_if_value_nonzero(
            event_data, 'end_time', encode_export_date(event.end_time, tzlocal))
        dict_add_if_value_nonzero(event_data, 'url', event.url)
        dict_add_if_value_nonzero(
            event_data, 'description', event.description)
        clean_json_dictionary_value(event_data, 'description')
        if event.location:
            dict_add_if_value_nonzero(
                event_data, 'location_key', event.location.key)
        dict_add_if_value_nonzero(
            event_data, 'description_fi', event.description_fi)
        clean_json_dictionary_value(event_data, 'description_fi')
        flags = []
        if event.canceled:
            flags.append("canceled")
        flags.extend(event.flags.split(","))
        flags = [flag.strip() for flag in flags]
        event_data['flags'] = flags
        event_data['categories'] = [
            category.strip() for category in event.categories.split(",")]
        events.append(event_data)
    result['events'] = events

    data = json.dumps(result)
    return HttpResponse(data, mimetype="application/javascript")


class AsmCsvImportForm(forms.Form):
    subject = forms.CharField(label=u"Assembly CSV data", widget=forms.Textarea)


@require_party
@permission_required('schedule.admin')
def importasmcsv(request):
    success = False
    if request.method != 'POST':
        form = AsmCsvImportForm()
        return render_to_response(
            "importasmcsvform.html", {
                'form':form,
                'success':success
                },
            context_instance=RequestContext(request)
            )

    form = AsmCsvImportForm(request.POST)
    if not form.is_valid():
        return render_to_response(
            "locations_createform.html", {
                'form':form,
                'success':success
                },
            context_instance=RequestContext(request)
            )

    try:
        location = form.save(commit=False)
        location.save()
    except Exception as e:
        print e
        return
    success = True
    return admin(request, location.pk, True, 'Location created', party=request.party)
    
    
