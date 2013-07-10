import subprocess, pickle, threading,traceback 
import logging, time
from contextlib import closing
from xml.sax.saxutils import escape

from pywps import util
from pywps.models import Jobs, STATUS, JOBTOWPSSTATUS

class NotInitialException(Exception):
    pass

class Job:
    """
    base class of job. Job was used to manage the status updating of process
    
    @var responseObj: Response Document object that composite response document of execute request
    """
    def __init__(self, process, responseObj):
        self._process = process
        self._response = responseObj
        self._popen = None
        self._task = None
    
    @property
    def status(self):
        self.InitialedCheck()
        return self._task.status
        
    @property
    def traceback(self):
        self.InitialedCheck()
        return self._task.traceback
        
    @property
    def error(self):
        self.InitialedCheck()
        return self._task.stderr
    
    @property
    def stdout(self):
        self.InitialedCheck()
        return self._task.stdout
    
    @property
    def isInterrupt(self):
        self.InitialedCheck()
        return self._task.interrupt
    
    @property
    def statusLocation(self):
        self.InitialedCheck()
        return self._task.statusLocation
    
    @property
    def response(self):
        self.InitialedCheck()
        return self._task.response

    def _setStatus(self, v):
        self.InitialedCheck()
        assert v in STATUS
        
        # update file of status
        if v == 'SUCCESSED':
            self._updateSuccessed()
        elif v == 'FAILED':
            self._updateFailed()
        else:
            self._updateOthersStatus(v)
        
        self._task.status = v    
        # TODO: in the _doing thread an exception will be throwed when save
        self._task.save()
    
    def InitialedCheck(self):
        if not self._task or self._task.status == 'INITIALLING':
            raise NotInitialException("This job haven't initialed")
        
    def Initial(self, request_method, request, interrupt, statusLocation = None):
        """
        initial job with inputs and statuslocation file if the request is asynchromous method
        
        @param  interrupt: it's true if request is asynchromous and @{statusLocation} must be setted 
        """
        
        if interrupt:
            assert statusLocation
        self._task = Jobs.objects.create(request_method = request_method, 
                                         request = request, interrupt = interrupt, 
                                         process = self._process.model,
                                         statusLocation = statusLocation)
        
        self._task.status = 'INITIALLING'
        
        if interrupt:
            pass              
            #settings.jobsMng.putJob(self)
        
        self._task.status = 'INITIALED'
        
        return self.status
    
    def start(self):
        self._setStatus( 'STARTING' )

        # get command and start execute
        cmd = self._process.getCmd()
        
        logging.info('command of execute is {0}'.format(cmd))
        
        self._task.cmd = pickle.dumps(cmd)
        
        self._p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE )
        
        self._setStatus( 'EXECUTING' )

        # wait for this thread terminate
        if not self.isInterrupt:
            while(self._p.poll() == None):
                time.sleep(1)
        
            if self._p.poll()==0:
                (self._task.stdout, self._task.stderr) = self._p.communicate()
                self._process.OutputReset()
                self._setStatus( 'SUCCESSED' )
            elif self._p.poll() == 1:
                (self._task.stdout, self._task.stderr) = self._p.communicate()
                self._setStatus( 'FAILED' )
            
        return
        
    def stop(self):
#        p = subprocess.pickle.loads(self._task.pickled_string)

        if isInterrupt and self.status == 'EXECUTING':
            self._setStatus( 'STOPPING' )
            self._p.send_signal(subprocess.signal.SIGSTOP)
            self._setStatus( 'STOPPED' )
            
        return self.status
        
    def restart(self):
        if isInterrupt and ( self.status == 'STOPPED' or self.status == 'EXECUTING'):
            self._setStatus( 'RESTARTING' )
            self._p = subprocess.Popen(pickle.loads(self._task.cmd), stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=None)
            self._setStatus( 'RESTARTED' )
            
        return self.status
        
    def cancel(self):
        if isInterrupt and (self.status != 'FAILED' or self.status != 'SUCCESSED'):
            self._setStatus( 'CANCELLING' )
            self._p = subprocess.Popen(pickle.loads(self._task.cmd), stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=None)
            self._setStatus( 'CANCELLED' )
            
        return self.status
        
    def _doing(self, p, post_success=None):
        """
        executing until process over or status changed
        
        @param p: instance of Popen
        @param post_success: operation method after this process execute successful 
        """
        while(p.poll() == None):
            time.sleep(1)
        
        if self.status == 'EXECUTING':
            if p.poll()==0:
                (self._task.stdout, self._task.stderr) = p.communicate()
                post_success()
                self._setStatus( 'SUCCESSED' )
            elif p.poll() == 1:
                (self._task.stdout, self._task.stderr) = p.communicate()
                self._setStatus( 'FAILED' )
                
                # TODO: need add the traceback information to Job
        return
        
#    def updateStatus(self):
#        """
#        save response to Job and update statusLocation file for async request
#        
#        Note: @{self._task.status} can't change to @{self.status} 
#        """
#        if self._task.status == 'SUCCESSED':
#            self._updateSuccessed()
#        elif self._task.status == 'FAILED':
#            self._updateFailed()
#        else:
#            self._updateOthersStatus()
        
    def _updateSuccessed(self):
        if self.isInterrupt:
            assert self.statusLocation
            self._task.response = self._response.successedResponseDocument( escape(self.stdout), 
                                                util.statusLocationFiletoUrl(self.statusLocation))
            with closing( open(self.statusLocation, 'w') ) as f:
                f.write(self.response)
        else:
            self._task.response = self._response.successedResponseDocument(escape(self.stdout))
            
    def _updateFailed(self):
        if self.isInterrupt:
            self._task.response = self._response.statusResponseDocument(JOBTOWPSSTATUS['FAILED'], 
                                escape(self.error), util.statusLocationFiletoUrl(self.statusLocation))
            assert self.statusLocation
            with closing( open(self.statusLocation, 'w') ) as f:
                f.write(self.response)
        else:
            self._task.response = self._response.statusResponseDocument(JOBTOWPSSTATUS['FAILED'], 
                                escape(self.error))
        
    def _updateOthersStatus(self, status):
        if self.isInterrupt:
            self._task.response = self._response.statusResponseDocument(JOBTOWPSSTATUS[status], 
                                self.stdout, util.statusLocationFiletoUrl(self.statusLocation))
            assert self.statusLocation
            with closing( open(self.statusLocation, 'w') ) as f:
                f.write(self.response)
        else:
            self._task.response = self._response.statusResponseDocument(JOBTOWPSSTATUS[status],
                                self.stdout)
        
class NormalProcessJob(Job):
    pass    