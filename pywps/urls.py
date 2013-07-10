from django.conf.urls import patterns, include, url
from pywps.views import *

urlpatterns = patterns('pywps', 
                       url('stdapi/?$', WpsStandardServiceApi.as_view(), name='wps_service'),
                       url('rest/jobs/$', JobsRestApi.as_view(), name = 'jobs_list'), 
                       url('rest/status/(?P<jobid>[\d]+?)/$', JobStatusRestApi.as_view(), name='job_status'),
                       url('rest/cancel/(?P<jobid>[\d]+?)/$', JobCancelRestApi.as_view(), name='job_cancel'),
                       url('rest/stop/(?P<jobid>[\d]+?)/$', JobStopRestApi.as_view(), name='job_stop'),
                       url('rest/restart/(?P<jobid>[\d]+?)/$', JobRestartRestApi.as_view(), name='job_restart'),
                       )