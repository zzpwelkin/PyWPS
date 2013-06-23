from django.conf.urls import patterns, include, url

urlpatterns = patterns('pywps', 
                       url('rest/jobs/$', ), 
                       url('rest/status/(?P<jobid>[\d]+?)/$', JobStatusRestApi.as_view(), name='job_status'),
                       url('rest/cancel/(?P<jobid>[\d]+?)/$', JobCancelRestApi.as_view(), name='job_cancel'),
                       url('rest/stop/(?P<jobid>[\d]+?)/$', JobStopRestApi.as_view(), name='job_stop'),
                       url('rest/restart/(?P<jobid>[\d]+?)/$', JobRestartRestApi.as_view(), name='job_restart'),
                       )