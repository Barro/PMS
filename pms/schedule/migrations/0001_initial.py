# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Adding model 'Event'
        db.create_table('schedule_event', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=255, null=True, blank=True)),
            ('time', self.gf('django.db.models.fields.DateTimeField')()),
            ('end_time', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
            ('location_url', self.gf('django.db.models.fields.URLField')(max_length=200, null=True, blank=True)),
            ('location', self.gf('django.db.models.fields.CharField')(max_length=255, null=True, blank=True)),
            ('hidden', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('schedule', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['schedule.Schedule'])),
        ))
        db.send_create_signal('schedule', ['Event'])

        # Adding model 'Schedule'
        db.create_table('schedule_schedule', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(unique=True, max_length=255)),
            ('party', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['party.Party'])),
        ))
        db.send_create_signal('schedule', ['Schedule'])

        # Adding model 'EventHistory'
        db.create_table('schedule_eventhistory', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('action', self.gf('django.db.models.fields.CharField')(max_length=1)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('changes', self.gf('django.db.models.fields.CharField')(max_length=2048, null=True, blank=True)),
            ('schedule', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['schedule.Schedule'])),
            ('time', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime(2012, 2, 24, 13, 37, 48, 231587))),
        ))
        db.send_create_signal('schedule', ['EventHistory'])


    def backwards(self, orm):
        
        # Deleting model 'Event'
        db.delete_table('schedule_event')

        # Deleting model 'Schedule'
        db.delete_table('schedule_schedule')

        # Deleting model 'EventHistory'
        db.delete_table('schedule_eventhistory')


    models = {
        'party.party': {
            'Meta': {'object_name': 'Party'},
            'active': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'big_icon': ('django.db.models.fields.URLField', [], {'max_length': '200', 'null': 'True', 'blank': 'True'}),
            'css': ('django.db.models.fields.URLField', [], {'max_length': '256', 'null': 'True', 'blank': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {'max_length': '1024', 'blank': 'True'}),
            'end_date': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'header_icon': ('django.db.models.fields.URLField', [], {'max_length': '200', 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'maintenance': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '1024'}),
            'name_visible': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'privacy_link': ('django.db.models.fields.URLField', [], {'max_length': '200', 'null': 'True', 'blank': 'True'}),
            'shortname': ('django.db.models.fields.CharField', [], {'max_length': '16'}),
            'slug': ('django.db.models.fields.SlugField', [], {'max_length': '50', 'db_index': 'True'}),
            'start_date': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'ticket_required': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'url': ('django.db.models.fields.URLField', [], {'max_length': '200', 'blank': 'True'})
        },
        'schedule.event': {
            'Meta': {'ordering': "['time', 'name']", 'object_name': 'Event'},
            'end_time': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'hidden': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'location': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'location_url': ('django.db.models.fields.URLField', [], {'max_length': '200', 'null': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'schedule': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['schedule.Schedule']"}),
            'time': ('django.db.models.fields.DateTimeField', [], {})
        },
        'schedule.eventhistory': {
            'Meta': {'object_name': 'EventHistory'},
            'action': ('django.db.models.fields.CharField', [], {'max_length': '1'}),
            'changes': ('django.db.models.fields.CharField', [], {'max_length': '2048', 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'schedule': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['schedule.Schedule']"}),
            'time': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(2012, 2, 24, 13, 37, 48, 231587)'})
        },
        'schedule.schedule': {
            'Meta': {'object_name': 'Schedule'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '255'}),
            'party': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['party.Party']"})
        }
    }

    complete_apps = ['schedule']
