import subprocess, pickle, thread,traceback

import pywps
from pywps.jobs import registerJob
from pywps.models import Jobs, STATUS

class NotInitialException(Exception):
    pass

class Job:
    """
    base class of job. Job was used to manage the status updating of process
    """
    def __init__(self, process):
        self._process = process
        self._popen = None
        self._task = None
        #self._task = Jobs.objects.create(process = process._process)
        #self.Initialed()
        
#    def __init__(self, request_method, request, interrupt, process):
#        """
#        @param request_method: request method
#        @param request: string with GET method and xml/text with POST method
#        @param interrupt: it's should true for async request or may be stop or cancel 
#            by user when requester is waiting process terminate 
#        @param process: pywps.Process.WPSProcess instance
#        """
#        self._job_m = Jobs.objects.create(request_method = request_method, 
#                                          request = request, interrupt = interrupt, 
#                                          process = process._process)
    
    @property
    def status(self):
        self.InitialedCheck()
        return self._task.status
    
    @status.setter
    def status(self, v):
        self.InitialedCheck()
        assert v in STATUS
        self._task.status = v
        self._task.save()
        
    @property
    def traceback(self):
        self.InitialedCheck()
        return self._task.trackback
    
    @traceback.setter
    def traceback(self, v):
        self._task.traceback = v
        self._task.save()
        
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
    
    def InitialedCheck(self):
        if not self._task or self._task.status == 'INITIALLING':
            raise NotInitialException("This job haven't initialed")
        
    def Initial(self, request_method, request, interrupt):
        self._task = Jobs.objects.create(request_method = request_method, 
                                         request = request, interrupt = interrupt, 
                                         process = self._process.model)
        
        self._task.status = 'INITIALLING'
        if interrupt:                
            registerJob(self)
        self._task.status = 'INITIALED'
        
        return self._task.status
    
    def start(self):
        self._task.status = 'STARTING'

        # get command and start execute
        cmd = self._process.getCmd()
        
        self._task.cmd = pickle.dumps(cmd)
        
        self._p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=None)
        
        #self._task.pickled_string = subprocess.pickle.dumps(p)
        
        # continue executing until terminate or status is not EXECUTING
        thread.start_new_thread(self._doing, (self._p, self._process.OutputReset,) )
        
        self._task.status = 'EXECUTING'
        
    def stop(self):
#        p = subprocess.pickle.loads(self._task.pickled_string)

        if isInterrupt and self._task.status == 'EXECUTING':
            self._task.status = 'STOPPING'
            self._p.send_signal(subprocess.signal.SIGSTOP)
            self._task.status = 'STOPPED'
        
        return self._task.status
        
    def restart(self):
#        self._task.status = 'RESTARTING'
#        # TODO:
#        p = subprocess.Popen(pickle.loads(self._task.cmd), stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=None)
#        
#        thread.start_new_thread(self._doing, p)
#        
#        self._task.pickled_string = subprocess.pickle.dumps(p)
#        res = f(*argv, **kwargvs)
        if isInterrupt and self._task.status == 'STOPPED' or self._task.status == 'EXECUTING':
            self._task.status = 'RESTARTING'
            self._p = subprocess.Popen(pickle.loads(self._task.cmd), stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=None)
            self._task.status = 'RESTARTED'
            
        return self._task.status
        
    def cancel(self):
#        self._task.status = 'CANCELLING'
#        # TODO:
##        p = subprocess.pickle.loads(self._task.pickled_string)
#        p.send_signal(subprocess.signal.SIGTERM)
#        res = f(*argv, **kwargvs)
        if isInterrupt and self._task.status == 'EXECUTING':
            self._task.status = 'CANCELLING'
            self._p = subprocess.Popen(pickle.loads(self._task.cmd), stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=None)
            self._task.status = 'CANCELLED'
            
        return self._task.status
        
    def _doing(self, p, post_success=None):
        """
        executing until process over or status changed
        
        @param p: instance of Popen
        @param post_success: operation method after this process execute successful 
        """
        while(p.poll() == None):
                pass
        
        if self._task.status == 'EXECUTING':
            if p.poll()==0:
                (self._task.stdout, self._task.stderr) = p.communicate()
                post_success()
                self._task.status = 'SUCCESSED'
            elif p.poll() == 1:
                (self._task.stdout, self._task.stderr) = p.communicate()
                self._task.status = 'FAILED'
                
        thread.exit_thread()
            
        
class NormalProcessJob(Job):
    pass    