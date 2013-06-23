# Create your views here.

from django.views.generic import View

from pywps import jobs

class JobStatusRestApi(View):
    def get(self, request, *args, **kwargs):
        return HttpResponse('', 'json/text')
    
class JobCancelRestApi(View):
    def get(self, request, *args, **kwargs):
        job = jobs.getJob(kwargs['jobid'])
        job.cancel()
        return HttpResponse('', 'json/text')
    
class JobStopRestApi(View):
    def get(self, request, *args, **kwargs):
        job = jobs.getJob(kwargs['jobid'])
        job.stop()
        return HttpResponse('', 'json/text')
    
class JobRestartRestApi(View):
    def get(self, request, *args, **kwargs):
        job = jobs.getJob(kwargs['jobid'])
        job.restart()
        return HttpResponse('', 'json/text')
