from django.db import models
from django import forms
from datetime import timedelta,datetime
from django.db.models.signals import pre_save,pre_delete
from django.dispatch import receiver
from django.forms.models import model_to_dict
import django.dispatch

# Create your models here.
import django.dispatch

#there might be event priority classes in the future
#e.g. important, normal, unimportant

schedule_updated = django.dispatch.Signal()

class Schedule(models.Model):
	name = models.CharField(max_length=255,unique=True)

	party = models.ForeignKey('party.Party')
#	 events = models.ManyToManyField(Event)
	

	def __unicode__(self):
		return self.name
	class Meta:
		permissions = (
			('admin','admin schedule'),
			('manage','manage schedule'),
		)


class Location(models.Model):
	name = models.CharField(max_length=255, blank=False, null=False)
	url = models.URLField(blank=True, null=True)
	description = models.TextField(blank=True)

	schedule = models.ForeignKey('schedule.Schedule')

	def __unicode__(self):
		return u"%s (%s)" % (self.name, self.schedule)

	# i18n
	name_fi = models.CharField(u"Nimi suomeksi", max_length=255, blank=True, null=True)
	description_fi = models.TextField(u"Kuvaus suomeksi", blank=True)

	class Meta:
		ordering = ["schedule", "name"]
		permissions = (
			('admin','admin schedule locations'),
			('manage','manage schedule locations'),
		) 

class Event(models.Model):
	name = models.CharField(max_length=255, blank=True, null=True)
	time = models.DateTimeField()
	end_time = models.DateTimeField(blank=True, null=True, help_text="Default is start_time + 5 minutes")
	original_time = models.DateTimeField(help_text=u"Can not be set when creating an event.")
	url = models.CharField(max_length=255, blank=True)
	description = models.TextField(blank=True)
	hidden = models.BooleanField(default=False)
	canceled = models.BooleanField(default=False)
	cancel_reason = models.TextField(u"Cancellation reason", blank=True)
	categories = models.CharField("Comma separated list of tag-like categories.", max_length=255, blank=True)
        order = models.FloatField(default=0.0)
#        major = models.BooleanField(default=False)
#        bigscreen = models.BooleanField(default=False)
#        class_ = models.TextField(blank=True)
#        asmtv = models.BooleanField(defauls=False)

	# i18n
	name_fi = models.CharField(u"Nimi suomeksi", max_length=255, blank=True, null=True)
	description_fi = models.TextField(u"Kuvaus suomeksi", blank=True)

	location = models.ForeignKey('schedule.Location', null=True)
	schedule = models.ForeignKey('schedule.Schedule')

	def save(self, *args, **kwargs):
		super(Event, self).save(*args, **kwargs)

	def __unicode__(self):
		return u"%s %s" % (self.name,self.time)

	def default_original_time(self):
		return self.time

	def default_end(self):
		"""
		Default end time is start time + 5 minutes so events without a
		duration will show for 5 minutes after.
		"""
		return self.time + timedelta(minutes=5)
	
	def is_active(self):
		"""
		Is the event ongoing. An event without end time is considered active 5
		minutes after it started.
		"""
		now = datetime.now()
		
		if not self.end_time:
			return now >= self.time and self.time < now+timedelta(minutes=5)

		return self.time <= now and self.end_time > now
 
	def is_close_to_end(self):
		"""
		In case we want to hilight ending opportunities like voting deadlines.
		"""
		return self.is_active() and self.end_time and self.end_time < datetime.now() + timedelta(minutes=15)

	def has_passed(self):
		now = datetime.now()
		
		if not self.end_time:
			return now > self.time+timedelta(minutes=5)
		
		return now > self.end_time + timedelta(minutes=15)

	class Meta:
		ordering = ["time", "name"]
		permissions = (
			('admin','admin schedule events'),
			('manage','manage schedule events'),
		) 


@receiver(pre_save, sender=Event, dispatch_uid="unique_event_presave")
def event_onsave(sender, instance, raw, **kwargs):
	try:
		try:
			ev = Event.objects.get(pk=instance.pk)
			changes = "" 
			instancedict = model_to_dict(instance)
			evdict = model_to_dict(ev)
			for name in instancedict.keys():
				if evdict[name] != instancedict[name]:
					changes += """%s: %s -> %s\n""" % (name, evdict[name], 
						instancedict[name])
			hist = EventHistory(action="M", name=ev.name,
			changes=changes, schedule=instance.schedule)
			schedule_updated.send_robust(sender=instance)
			
		except Event.DoesNotExist:
			hist = EventHistory(action="C", name=instance.name,
			schedule=instance.schedule)
		hist.save()
	except Exception as e:
		#print e
		pass

@receiver(pre_delete, sender=Event, dispatch_uid="unique_event_predelete")
def event_ondelete(sender, instance, using, **kwargs):
	hist = EventHistory(action="D", name=instance.name,
						schedule=instance.schedule)
	hist.save()

class EventHistory(models.Model):
	"""
	Changes made to event	 
	"""
	ACTION_TYPE = (
		('M','Modify'),
		('C','Create'),
		('D','Delete'),
	)

	action = models.CharField(max_length=1, choices=ACTION_TYPE) #old name
	name = models.CharField(max_length=255) #old name
	changes = models.CharField(max_length=2048,null=True,blank=True) #old name
	schedule = models.ForeignKey('Schedule')
	time = models.DateTimeField(default=datetime.now())


class EventForm(forms.ModelForm):
	class Meta:
		model = Event
		#exclude = ('original_time',)


class LocationForm(forms.ModelForm):
	class Meta:
		model = Location
