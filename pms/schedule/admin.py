from django.contrib import admin
import time

from models import Schedule, Event, Location

#class ScheduleInline(admin.StackedInline):
#    model = Schedule.events.through
#    extra = 1

#class EventAdmin(admin.ModelAdmin):
#    inlines = [ScheduleInline]
class EventAdmin(admin.ModelAdmin):
    list_per_page = 10000
    list_display = ('name', 'starttime', 'endtime')
    def starttime(self, obj):
        return obj.time.strftime("%A %d. %B %Y %H:%M")

    def endtime(self, obj):
        if (obj.time.strftime("%d") == obj.end_time.strftime("%d")):
            return obj.end_time.strftime("%H:%M")
	else:
            return obj.end_time.strftime("%A %H:%M")
    class Media:
        js = ("eventadmin.js",)

admin.site.register(Schedule)
admin.site.register(Location)
admin.site.register(Event, EventAdmin)
#admin.site.register(Event, EventAdmin)
