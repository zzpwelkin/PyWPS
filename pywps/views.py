# Create your views here.
import os, logging

from django.utils import simplejson as json
from django.views.generic import View
from django.conf import settings
from django.http import HttpResponse

from Pywps import  Pywps
import models
from Exceptions import WPSException

class WpsStandardServiceApi(View):
    """
    standard WPS service api,e.g getcapabilities, describeprocess and execute
    """
    def wps_request(self, req, wps_cfg):
        """
        requst from local wps service and reponse the result documennt of processed
        
        @param  req: HttpRequest instance
        @param wps_cfg: the configure file that pywps need
           
        @return: an string document
        """
        res = 'Error'
        inputQuery = req.META['QUERY_STRING']
        logging.info("Query of wps service is : {0}".format(inputQuery))
    
        if not inputQuery:
            err =  NoApplicableCode("No query string found.")
            res = err.__str__()
            
        # create the WPS object
        os.environ['PYWPS_CFG'] = wps_cfg
        try:
            # setting configure file from Pywps initial not effect
            wps = Pywps(req.method, wps_cfg)
            if wps.parseRequest(inputQuery):
                res = wps.performRequest()
            else:
                msg = "wps service parse request failed! "
                logger.warn(msg)
                res = msg
        except WPSException,e:
            res = e.__str__()
    
        return res
    
    def get(self, request, *args, **kwargs):
        return HttpResponse (self.wps_request(request, settings.PYWPS_CFG), mimetype='application/xml')
    
    def post(self, request, *args, **kwargs):
        return HttpResponse (self.wps_request(request, settings.PYWPS_CFG), mimetype='application/xml')
    
class JobsRestApi(View):
    """
    response all the job and it's status, stdout,i.e.
    """
    def get(self, request, *args, **kwargs):
        res = {}
        
        def info(job):
            kv = {'create time':job.create_time,'execution time':job.execution_time, 'update time':job.update_time, 
                  'request_method':job.request_method, 'request':job.request, 'response':job.response, 
                  'stdout':job.stdout, 'stderr':job.stderr, 'status':job.status}
                  
        for job in models.Job.objects.all():
            res[job.pk] = self.info(job)
            
        return HttpResponse(json.dumps(res), mimetype='application/json')
        
class JobStatusRestApi(View):
    def get(self, request, *args, **kwargs):
        job = jobmanager.getJobMng().getJob(kwargs['jobid'])
        return HttpResponse(job.response, mimetype='application/xml')
    
class JobCancelRestApi(View):
    def get(self, request, *args, **kwargs):
        job = jobmanager.getJobMng().getJob(kwargs['jobid'])
        job.cancel()
        return HttpResponse(job.response, mimetype='application/xml')
    
class JobStopRestApi(View):
    def get(self, request, *args, **kwargs):
        job = jobmanager.getJobMng().getJob(kwargs['jobid'])
        job.stop()
        return HttpResponse(job.response, mimetype='application/xml')
    
class JobRestartRestApi(View):
    def get(self, request, *args, **kwargs):
        job = jobmanager.getJobMng().getJob(kwargs['jobid'])
        job.restart()
        return HttpResponse(job.response, mimetype='application/xml')
