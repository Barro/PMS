from django.contrib import admin

from models import Schedule, Event, Location

#class ScheduleInline(admin.StackedInline):
#    model = Schedule.events.through
#    extra = 1

#class EventAdmin(admin.ModelAdmin):
#    inlines = [ScheduleInline]
class EventAdmin(admin.ModelAdmin):
	list_per_page = 10000

admin.site.register(Schedule)
admin.site.register(Location)
admin.site.register(Event, EventAdmin)
#admin.site.register(Event, EventAdmin)
