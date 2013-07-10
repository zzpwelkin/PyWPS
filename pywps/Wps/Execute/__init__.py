"""
.. data:: TEMPDIRPREFIX

    prefix of temporary pywps directory

"""
# Author:	Jachym Cepicky
#        	http://les-ejk.cz
#               jachym at les-ejk dot cz
# License:
#
# Web Processing Service implementation
# Copyright (C) 2006 Jachym Cepicky
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301  USA

# set the sys.path to pywps
__all__ = ["UMN"]

import sys,os
#sys.path.append(
#    os.path.join(
#        os.path.dirname( os.path.abspath(__file__)) ,"..","..","..")
#    )

sys.path[0]= os.path.join(os.path.dirname( os.path.abspath(__file__)) ,"..","..","..")
import thread
import pywps
from pywps.models import JOBTOWPSSTATUS
from pywps.Process.InAndOutputs import ComplexOutput

import pywps.Ftp
from pywps import config
from pywps.Wps import Request
from pywps.Template import TemplateProcessor
import time,tempfile,re,types, base64, traceback,string
from shutil import copyfile as COPY
from shutil import rmtree as RMTREE
import logging, StringIO

from pywps import jobs, util
from pywps.jobs.jobs import Job
from pywps.Wps.Execute import UMN
from pywps.Wps.Execute import MapServerFactory

import pickle, subprocess

from xml.sax.saxutils import escape

TEMPDIRPREFIX="pywps-instance"

accepted = "processaccepted"
started = "processstarted"
succeeded = "processsucceeded"
paused = "processpaused"
failed = "processfailed"

#Note: saxutils to escape &,< and > from URLs. Applied to _lineageComplexRerenceInput,_asReferenceOutput. in the last case
# it as been applied to ALL references, just as precausion

class Execute(Request):
    """
    This class performs the Execute request of WPS specification and
    formats output

    :param wps: :class:`pywps.Pywps`

    .. attribute :: accepted

        Process accepted indicator string
        
    .. attribute :: started

        Process started indicator string

    .. attribute :: succeeded

        Process succeeded indicator string

    .. attribute :: paused

        Process paused indicator string

    .. attribute :: failed

        Process failed indicator string

    .. attribute :: curdir

        Curent working directory, when the process is started

    .. attribute :: pid

        Id of currently running process on the system level

    .. attribute :: id

        Unique WPS Process identification

    .. attribute :: statusLocation

        Location, where status and response files are stored

    .. attribute :: outputFileName

        Name of the file, where status informations are printed to

    .. attribute :: outputFile

        List of file objects, where status informations are printed to

    .. attribute :: storeRequired

        Storing of process results is required

    .. attribute :: statusRequired

        Process should run in assynchronous mode

    .. attribute :: lineageRequired

        Include input and output description to final response document
        (just like DescribeProcess would do it)

    .. attribute :: status

        Current process status,  one of :attr:`processaccepted`,
        :attr:`processstarted`, :attr:`processsucceeded`, :attr:`processfailed`

    .. attribute :: statusMessage
        
        Text message or comment to particular status
        
    .. attribute :: percent

        Percent done

    .. attribute :: exceptioncode

        Code of exception

    .. attribute :: locator

        Locator of exception

    .. attribute :: statusTime

        current status time 

    .. attribute :: dirsToBeRemoved

        List of directories, which should be removed, after the process is
        successfully calculated

    .. attribute :: workingDir

        working directory, where the calculation is done

    .. attribute :: grass

        :class:`pywps.Grass.Grass`

    .. attribute :: rawDataOutput

        indicates, if there is any output, which should be returned
        directly (without final xml response document)
        
    .. attribute :: mapserver
    
        :class pywps.Wps.Execute.Mapserver
        
        Map server instance , for saving and public spatial data
    """

    # status variants
#    accepted = "processaccepted"
#    started = "processstarted"
#    succeeded = "processsucceeded"
#    paused = "processpaused"
#    failed = "processfailed"
    curdir = os.path.abspath(os.path.curdir)

    # running process id
    pid = None

    # session ID
    id = ''

    # status location and file
    statusLocation = ''
    outputFileName = None
    outputFile = None

    # process status
    storeRequired = False # should the request run asynchronously?
    statusRequired = False # should the status file be updated?
    lineageRequired = False # should the output have lineage?
    #status = None
    statusMessage = None
    percent = 0
    exceptioncode = None
    locator = 0
    #statusTime = None
    responseObj = None
    job = None

    #__pickleFileName = "state-pywps"
    __statusFileName = "state-pywps"

    # directories, which should be removed
    dirsToBeRemoved = []

    # working directory and grass
    workingDir = ""

    rawDataOutput = None
    
    def parseResponseDocument(self):
        """
        parse response document
        """
        # rawDataOutput
        if len(self.wps.inputs["responseform"]["rawdataoutput"])>0:
            self.rawDataOutput = self.wps.inputs["responseform"]["rawdataoutput"].keys()[0]

        # is status required
        self.statusRequired = False
        if self.wps.inputs["responseform"]["responsedocument"].has_key("status"):
            if self.wps.inputs["responseform"]["responsedocument"]["status"]:
                self.statusRequired = True

        # is store response required ?
        self.storeRequired = False
        if self.wps.inputs["responseform"]["responsedocument"].has_key("storeexecuteresponse"):
            if self.wps.inputs["responseform"]["responsedocument"]["storeexecuteresponse"]:
                outputType = "file" 
                outputPath = config.getConfigValue("server","outputPath")
                # Check for ftp storage
                if string.find(outputPath.lower(), "ftp://", 0, 6) == 0:
                    outputType = "ftp"
                    
                if outputType == "file":
                    try:
                        self.outputFile = open(self.outputFileName,"w")
                    except Exception, e:
                        traceback.print_exc(file=pywps.logFile)
                        self.cleanEnv()
                        raise pywps.NoApplicableCode(e.__str__())
                # Set up the response document ftp object
                
                elif outputType == "ftp":
                    
                    try:
                        ftpHost = outputPath[6:]
                        ftplogin = config.getConfigValue("server","ftplogin")
                        ftppasswd= config.getConfigValue("server","ftppasswd")
                        ftpConnection = pywps.Ftp.FTP(ftpHost,port=6666)
                        ftpConnection.setFileName(os.path.basename(self.outputFileName))
                        ftpConnection.login(ftplogin, ftppasswd)
                        # Close to avoid time out, the response call will reconnect and relogin
                        ftpConnection.close()
                        self.outputFile = ftpConnection
                    except Exception, e:
                        traceback.print_exc(file=pywps.logFile)
                        self.cleanEnv()
                        raise pywps.NoApplicableCode("FTP error: " +  e.__str__())


                self.storeRequired = True

        if self.storeRequired:
            self.statusLocation = config.getConfigValue("server","outputUrl")+"/"+self.getSessionId()+".xml"

        # is lineage required ?
        self.lineageRequired = False
        if self.wps.inputs["responseform"].has_key("responsedocument"):
            if self.wps.inputs["responseform"]["responsedocument"].has_key("lineage") and \
                self.wps.inputs["responseform"]["responsedocument"]["lineage"] == True:
                self.lineageRequired = True
                 
    def SetValueToProcess(self):
        """
        set input values to input objects and initial output objects of process  
        """
        # download and consolidate data
        self.consolidateInputs()
        # set output data attributes defined in the request
        self.consolidateOutputs()
    

    def __init__(self,wps, processes=None ):

        Request.__init__(self,wps,processes)

        self.wps = wps
        self.process = None

        # initialization
        #self.statusTime = time.localtime()
        self.pid = os.getpid()
        #self.status = None
        self.outputFileName = os.path.join(config.getConfigValue("server","outputPath"),self.getSessionId()+".xml")
    
        self.parseResponseDocument()

        # setInput values
        self.initProcess()
        
        # create the ResponseDocument object
        try:
            self.responseObj = ResponseDocument( self.templateProcessor, self.getSessionId(), 
                                           self.process, util.serviceInstanceUrl(config.getConfigValue("wps","serveraddress")), 
                                           'utf-8', 'en', self.wps.inputs.get("datainputs", []), 
                                           self.wps.inputs["responseform"]["responsedocument"].get("outputs", []), 
                                           self.rawDataOutput, self.storeRequired,
                                           self.statusRequired, self.lineageRequired)
            # init environment variable
            self.initEnv()

            # set values to process
            self.SetValueToProcess()
            
            # Execute
            self.executeProcess()
            
        # remove all temporary files
        finally:
            self.cleanEnv()

    def initProcess(self):
        """Setting and controlling input values, set by the client. Also the
        processes from PYWPS_PROCESS directory or default directory is
        imported.
        """

        # import the right package
        self.process = None
        try:
            self.process = self.getProcess(self.wps.inputs["identifier"])
        except Exception, e:
            self.cleanEnv()
            raise pywps.InvalidParameterValue(
                    self.wps.inputs["identifier"])

        if not self.process:
            self.cleanEnv()
            raise pywps.InvalidParameterValue(
                    self.wps.inputs["identifier"])

        # set proper method for status change
        #self.process.pywps = self.wps
        #self.process.status.onStatusChanged = self.onStatusChanged
        self.process.debug = config.getConfigValue("server","debug")
        self.process.logFile = pywps.logFile
        
    def initJob(self, isAsync):
        """
        It's needed before execute and after process initial successful that initial a job for this request.
        
        @param isAsync: it's true if the request is aysnc method others is false
        """
        assert self.process
        
        statusLocation = None
        if isAsync:
            tmpPath = config.getConfigValue("server","tempPath")
            statusLocation = os.path.join(tmpPath, self.__statusFileName+"-"+str(self.wps.UUID))
            #statusLocation = self.statusLocation
        
        self.job = self.process.createJob(self.responseObj)
        if not self.job.Initial(self.wps.method, str(self.wps.inputs), isAsync, self.outputFileName) == 'INITIALED':
            logging.warning("job initial failed")
            raise Exception("job initial failed")
        
        return self.job

    def consolidateInputs(self):
        """ Donwload and control input data, defined by the client """
        # calculate maximum allowed input size
        maxFileSize = util.calculateMaxInputSize(config.getConfigValue("server","maxfilesize"))

        # set input values
        for identifier in self.process.inputs:

            # Status
            self.responseObj.promoteStatus(paused, statusMessage="Getting input %s of process %s" %\
                    (identifier, self.process.identifier))

            input = self.process.inputs[identifier]
            
            # exceptions handler
            #input.onProblem = self.onInputProblem
            # maximum input file size must not be greater, than the one,
            # defined in the global config file
            
            if input.type == "ComplexValue":
                #if maxfile == 0 then we have no limits
                if maxFileSize==0:
                    input.maxFileSize=0
                else:
                    if not input.maxFileSize or input.maxFileSize > maxFileSize:
                        input.maxFileSize = maxFileSize
                #if maxFile not present or bigger than value in config value

            try:
                if self.wps.inputs["datainputs"]:
                    for inp in self.wps.inputs["datainputs"]:
                        if unicode(inp["identifier"]) == unicode(identifier):
                             #In complexValue trying to set the mimeType from user definition
                            # --> cant be here
                            if input.type == "ComplexValue": 
                                input.setMimeType(inp)
                            
                            #Passing value/content
                            resp = input.setValue(inp)
                            if resp:
                                self.cleanEnv()
                                raise pywps.InvalidParameterValue(resp)
            except KeyError,e:
                pass

        # make sure, all inputs do have values
        for identifier in self.process.inputs:
            input = self.process.inputs[identifier]
            if input.getValue() == None and input.minOccurs > 0:
                self.cleanEnv()
                raise pywps.MissingParameterValue(identifier)

    def consolidateOutputs(self):
        """Set desired attributes (e.g. asReference) for each output"""
        if self.wps.inputs["responseform"]["responsedocument"].has_key("outputs"):
            respOutputs = self.wps.inputs["responseform"]["responsedocument"]["outputs"]
            for identifier in self.process.outputs:
                poutput = self.process.outputs[identifier]
                respOut = None
                for out in respOutputs:
                    if out["identifier"] == identifier:
                        respOut = out

                if respOut:
                    poutputList=dir(poutput)
                    # asReference
                    if respOut.has_key("asreference") and \
                        "asReference" in poutputList:
                        poutput.asReference = respOut["asreference"]

                    #jmdj mimetype and not mimeType
                    if respOut.has_key("mimetype") and \
                        "format" in poutputList:
                        if respOut["mimetype"] != '':
                            poutput.format["mimetype"] = respOut["mimetype"]

                    # schema
                    if respOut.has_key("schema") and \
                        "format" in poutputList:
                        if respOut["schema"] != '':
                            poutput.format["schema"] = respOut["schema"]
                   
                    # encoding
                    if respOut.has_key("encoding") and \
                        "format" in poutputList:
                        if respOut["encoding"] != '':
                            poutput.format["encoding"] = respOut["encoding"]
                    
                    # uom
                    if respOut.has_key("uom") and \
                        "uom" in poutputList:
                        if respOut["uom"] != '':
                            poutput.uom = respOut["uom"]
                     
        #Even if the document response is not set
        #self.format has to be created and filled
        #Checking/resetting mimetype
        #poutput --> ComplexOutputObject
        for identifier in self.process.outputs:
            
            poutput = self.process.outputs[identifier]
            if poutput.type == "ComplexValue":
                #Only None if information is lacking
                [poutput.format.__setitem__(missing,None) for missing in [item for item in ("mimetype","schema","encoding") if item not in poutput.format.keys()]]
                poutput.checkMimeTypeIn()
                                 
#    def onInputProblem(self,what,why):
#        """This method is used for rewriting onProblem method of each input
#
#        :param what: locator of the problem
#        :param why: possible reason of the problem
#        """
#
#        exception = None
#
#        if what == "FileSizeExceeded":
#            exception = pywps.FileSizeExceeded
#        elif what == "NoApplicableCode":
#            exception = pywps.NoApplicableCode
#        elif what == "InvalidParameterValue":
#            exception = pywps.InvalidParameterValue
#        
#        self.cleanEnv()
#        raise exception(why)
#    
#    def onOutputProblem(self,what,why):
#        """This method logs the existance of problens in the complexData mainly (output mimeType?)
#        :param what: locator of the problem
#        :param why: possible reason of the problem
#        """
#        exception = None
#
#        if what == "FileSizeExceeded":
#            exception = pywps.FileSizeExceeded
#        elif what == "NoApplicableCode":
#            exception = pywps.NoApplicableCode
#        elif what == "InvalidParameterValue":
#            exception = pywps.InvalidParameterValue
#        
#        self.cleanEnv()
#        raise exception(why)

    def executeProcess(self):
        """Calls 'execute' method of the process, catches possible exceptions
        and set process failed or succeeded
        """
        try:
            # Asynchronous or Synchronous request
            # OGC 05-007r7 page 36, Table 50, note (a)
            # OGC 05-007r7 page 42
            if self.storeRequired and self.statusRequired:
                # initial job of this request
                self.initJob(True)
            else:
                self.initJob(False)
 
            self.job.start()

            if self.job.status == 'FAILED':
                # save traceback information
                tracf = StringIO.StringIO()
                traceback.print_exc(file = tracf)
                
                # write traceback to log file
                traceback.print_exc(file=pywps.logFile)
                
#                raise pywps.NoApplicableCode(
#                        "Failed to execute WPS process [%s]: %s" %\
#                                (self.process.identifier,processError))
            logging.info('Status is {0}'.format(self.job.status))
            self.response = self.job.response

        # re-raise WPSException, will be caught outside
        except pywps.WPSException,e:
            raise e

        except Exception,e:
            traceback.print_exc(file=pywps.logFile)
            raise pywps.NoApplicableCode(
                    "Failed to execute WPS process [%s]: %s" %\
                            (self.process.identifier,e))
                    
    def getSessionId(self):
        """ Returns unique Execute session ID

        :rtype: string
        :return: unique id::

            "pywps-"+uuid.uuid1()

        """
        return "pywps-"+self.wps.UUID

    def getSessionIdFromStatusLocation(self,statusLocation):
        """ Parses the statusLocation, and gets the unique session ID from it

        .. note:: Not in use, maybe should be removed.
        """
        begin = statusLocation.find("/pywps-")
        end = statusLocation.find(".xml")
        if begin > -1 and end > -1:
            return statusLocation[begin:end]
        else:
            return None

#    def onStatusChanged(self):
#        """This method is used for redefinition of self.process.status class
#        """
#
#        self.promoteStatus(self.process.status.code,
#                statusMessage="%s %s"%(self.process.status.code,self.process.status.value),
#                percent=self.process.status.percentCompleted)

    def initEnv(self):
        """Create process working directory, initialize GRASS environment,
        if required.

        """

        # find out number of running sessions
        maxOperations = int(config.getConfigValue("server","maxoperations"))
        tempPath = config.getConfigValue("server","tempPath")

        dirs = os.listdir(tempPath)
        pyWPSDirs = 0
        for dir in dirs:
            if dir.find(TEMPDIRPREFIX) == 0:
                pyWPSDirs += 1

        if pyWPSDirs >= maxOperations and\
            maxOperations != 0:
            raise pywps.ServerBusy(value="Maximal number of permitted operations exceeded")

        # create temp dir
        self.workingDir = tempfile.mkdtemp(prefix=TEMPDIRPREFIX, dir=tempPath)

        self.workingDir = os.path.join(
                config.getConfigValue("server","tempPath"),self.workingDir)

        os.chdir(self.workingDir)
        self.dirsToBeRemoved.append(self.workingDir)

#        # init GRASS
#        try:
#            if self.process.grassLocation:
#                from pywps import Grass
#                grass = Grass.Grass(self)
#                if self.process.grassLocation == True:
#                    self.process.grassMapset = grass.mkMapset()
#                elif os.path.exists(os.path.join(config.getConfigValue("grass","gisdbase"),self.process.grassLocation)):
#                    self.process.grassMapset = grass.mkMapset(self.process.grassLocation)
#                else:
#                    raise Exception("Location [%s] does not exist" % self.process.grassLocation)
#        except Exception,e:
#            self.cleanEnv()
#            traceback.print_exc(file=pywps.logFile)
#            raise pywps.NoApplicableCode("Could not init GRASS: %s" % e)

        return

    def cleanEnv(self):
        """ Removes temporary created files and dictionaries
        """
        
        os.chdir(self.curdir)
        def onError(*args):
            logging.error("Could not remove temporary dir")

        for i in range(len(self.dirsToBeRemoved)):
            dir = self.dirsToBeRemoved[0]
            if os.path.isdir(dir) and dir != "/":
                RMTREE(dir, onerror=onError)
                pass
            self.dirsToBeRemoved.remove(dir)
#        if self.spawned:
#            try:
#                tmpPath=config.getConfigValue("server","tempPath")
#                os.remove(os.path.join(tmpPath, self.__pickleFileName+"-"+self.wps.UUID))
#            except Exception, e:
#                logging.debug(str(e))
                    


class ResponseDocument:
    """
    composite response document for  ${process} with ${outputparam}
    
    @var _templateProcessor: a template engine that fill output, describe information of process to execute template
    @var _uuid: unique id identifier of request
    @var _process: instance of WPSProcess
    @var _mapserver: map server engine that will ouput the complexdata, as raster and vector, to one map server setted by admin
    @var _rawDataOutput: identifier of output of process that wanted return with raw form
    """
    
    _serviceUrl = ''
    _encoding = 'utf-8'
    _lang = 'en'
    _storeRequired = False # should the request run asynchronously?
    _statusRequired = False # should the status file be updated?
    _lineageRequired = False # should the output have lineage?
    _rawDataOutput = None # only one complex output is needed produce and its raw form returned directly
    _outputRequest = [] # the outputs that will be return
    _datainpus = [] # inputs
    
    def __init__(self, template, uuid, process, serviceUrl, encoding='utf-8', lang='en', datainputs=[], outputsRequest = [], rawDataOutput = None, storeRequired = False, statusRequired = False, 
                 lineageRequired = False):
        # check parameter
        self._checkParam(process, rawDataOutput, storeRequired, statusRequired, lineageRequired )
        
        self._templateProcessor = template
        self._uuid = uuid
        self._process = process
        
        # response document flag and intpus parameters
        self._serviceUrl = serviceUrl
        self._encoding = encoding
        self._lang = lang
        self._datainpus = datainputs
        self._outputRequest = outputsRequest
        
        if not self._outputRequest:
            self._outputRequest = self._process.outputs.keys()
            
        self._rawDataOutput = rawDataOutput
        self._storeRequired = storeRequired
        self._statusRequired = statusRequired
        self._lineageRequired = lineageRequired
        
        # get map server instance from MapServerFactory
        self._mapserver = MapServerFactory.getServer(self._process, self._uuid)
        
    def _checkParam(self, process, rawDataOutput, storeRequired, statusRequired, lineageRequired ):
        """
        check if service support function of request or some request parameter is not supported 
        """
        # check rawdataoutput against process
        if rawDataOutput and rawDataOutput not in process.outputs:
            raise pywps.InvalidParameterValue("rawDataOutput")

        # check storeExecuteResponse against process
        if storeRequired and not process.storeSupported:
            raise pywps.StorageNotSupported(
                "storeExecuteResponse is true, but the process does not support output storage")

        # check status against process
        if statusRequired and not process.statusSupported:
            raise pywps.InvalidParameterValue(
                "status is true, but the process does not support status updates")

        # OGC 05-007r7 page 43
        # if status is true and storeExecuteResponse is false, raise an exception
        if statusRequired and not storeRequired:
            raise pywps.InvalidParameterValue(
                "status is true, but storeExecuteResponse is false")
      
       #check storeExecuteResponse agains asReference=true
        if not process.storeSupported and self._outputRequest:
           #check the array for asreference': True
               if len([item for item in  self._outputRequest if ("asreference" in item and item["asreference"]==True) ]):
                   raise pywps.InvalidParameterValue("storeExecuteResponse is false, but output(s) are requested as reference(s)")
        
    def successedResponseDocument(self, msg, statusLocation=''):
        if not self._rawDataOutput:
            # base process information 
            self.responseBase(self._encoding, self._lang, self._serviceUrl, statusLocation)
            
            # if lineage
            if self._lineageRequired:
                self._templateProcessor.set("lineage",1)
                self.lineageInputs(self._datainpus)
                self.outputDefinitions(self._outputRequest)
                
            self.promoteStatus(JOBTOWPSSTATUS['SUCCESSED'], msg)
            # fill outputs
            self.processOutputs(self._outputRequest)

            # Response document
            self.response = self._templateProcessor.__str__()
        # if rawDataOutput is required
        else:
            self.setRawData()
            
        return self._templateProcessor.__str__()

    def statusResponseDocument(self,status, msg, statusLocation=''):
        # base process information 
        self.responseBase(self._encoding, self._lang, self._serviceUrl, statusLocation)
        self.promoteStatus(status, msg)
        
        return self._templateProcessor.__str__()
    
    def responseBase(self, encoding, lang, serviceInstanceUrl, statusLocation = ''):
        self._templateProcessor.set("encoding", encoding)
        self._templateProcessor.set("lang", lang)
        self._templateProcessor.set("statuslocation", statusLocation)
        self._templateProcessor.set("serviceinstance", serviceInstanceUrl)
        
        # Description
        self.processDescription()
        
    def processDescription(self):
        """ Fills Identifier, Title and Abstract, eventually WSDL, Metadata and Profile
        parts of the output XML document
        """

        self._templateProcessor.set("identifier", self._process.identifier)
        self._templateProcessor.set("title", self._process.i18n(self._process.title))
        if self._process.abstract:
            self._templateProcessor.set("abstract", self._process.i18n(self._process.abstract))
        if self._process.metadata:
            self._templateProcessor.set("Metadata", util.formatMetadata(self._process))
        if self._process.profile:
            profiles=[]
            if type(self._process.profile) == types.ListType:
                for profile in self._process.profile:
                    profiles.append({"profile":profile})
            else:
                profiles.append({"profile":self._process.profile})
            self._templateProcessor.set("Profiles", profiles)
        if self._process.wsdl:
            self._templateProcessor.set("wsdl", self._process.wsdl)
        if self._process.version:
            self._templateProcessor.set("processversion", self._process.version)
    
    def lineageInputs(self, datainputs):
        """Called, if lineage request was set. Fills the <DataInputs> part of
        output XML document.
        """
        templateInputs = []

        for identifier in self._process.inputs.keys():
            input = self._process.inputs[identifier]
            for wpsInput in datainputs:
                if wpsInput["identifier"] != identifier or\
                        wpsInput.has_key("lineaged"):
                    continue

                templateInput = {}
                wpsInput["lineaged"] = True
                
                templateInput["identifier"] = input.identifier
                templateInput["title"] = self._process.i18n(input.title)
                templateInput["abstract"] = self._process.i18n(input.abstract)
                
                if input.type == "LiteralValue":
                    templateInput = self._lineageLiteralInput(input,wpsInput,templateInput)
                elif input.type == "ComplexValue" and \
                       wpsInput.has_key("asReference") and wpsInput["asReference"] == True:
                    templateInput = self._lineageComplexReferenceInput(wpsInput,
                                                                input,templateInput)
                elif input.type == "ComplexValue":
                    templateInput = self._lineageComplexInput(wpsInput,templateInput)
                elif input.type == "BoundingBoxValue":
                    templateInput = self._lineageBBoxInput(input,templateInput)

                templateInputs.append(templateInput)
        self._templateProcessor.set("Inputs",templateInputs)

    def _lineageLiteralInput(self, input, wpsInput, literalInput):
        """ Fill input of literal data, boolean value will be cast to str
        """
        literalInput["literaldata"] = str(wpsInput["value"])
        literalInput["uom"] = input.uom
        return literalInput

    def _lineageComplexInput(self, wpsInput,complexInput):
        """ Fill input of complex data
        """
       
        #complexInput needs to be replicated
        complexInput["encoding"]=wpsInput["encoding"]
        complexInput["mimetype"]=wpsInput["mimetype"]
        complexInput["schema"]=wpsInput["schema"]
        complexInput["complexdata"]=wpsInput["value"]
        
        return complexInput

    def _lineageComplexReferenceInput(self, wpsInput, processInput, complexInput):
        """ Fill reference input

        :param wpsInput: associative field of self.wps.inputs["datainputs"]
        :param processInput: self.process.inputs
        """
        #URLS need to be quoted otherwise XML is not valid
        complexInput["reference"] = escape(wpsInput["value"])
        method = "GET"
        if wpsInput.has_key("method"):
            method = wpsInput["method"]
        complexInput["method"] = method
        complexInput["mimetype"] = processInput.format["mimetype"]
        complexInput["encoding"] = processInput.format["encoding"]
        if wpsInput.has_key("header") and wpsInput["header"]:
            complexInput["header"] = 1
            complexInput["key"] = wpsInput["header"].keys()[0]
            complexInput["value"] = wpsInput["header"][wpsInput["header"].keys()[0]]
        if wpsInput.has_key("body") and wpsInput["body"]:
            complexInput["body"] = wpsInput["body"]
        if wpsInput.has_key("bodyreference") and wpsInput["bodyreference"]:
            complexInput["bodyReference"] = wpsInput["bodyreference"]
        return complexInput

    def _lineageBBoxInput(self,input,bboxInput):
        """ Fill input of bbox data """
        
        bboxInput["bboxdata"] = 1
        bboxInput["crs"] = input.value.crs
        bboxInput["dimensions"] = input.value.dimensions
       
        #((minx,miny),(maxx, maxy))
        bboxInput["minx"] = input.value.coords[0][0]
        bboxInput["miny"] = input.value.coords[0][1]
        bboxInput["maxx"] = input.value.coords[1][0]
        bboxInput["maxy"] = input.value.coords[1][1]
        return bboxInput
    
    def outputDefinitions(self, outputsRequested):
        """Called, if lineage request was set. Fills the <OutputDefinitions> part of
        output XML document.
        """
        templateOutputs = []
        outputsRequested=self.getRequestedOutputs()
        
        for identifier in outputsRequested:
            templateOutput = {}
            output = self._process.outputs[identifier]

            templateOutput["identifier"] = output.identifier
            templateOutput["title"] = self._process.i18n(output.title)
            templateOutput["abstract"] = self._process.i18n(output.abstract)
            
            if self._process.storeSupported and output.asReference:
                templateOutput["asreference"] = "true"
            else:
                templateOutput["asreference"] = "false"

            templateOutputs.append(templateOutput);

            if output.type == "LiteralValue":
                templateOutput = self._lineageLiteralOutput(output,templateOutput)
                templateOutput["literaldata"] = 1
            elif output.type == "ComplexValue":
                templateOutput = self._lineageComplexOutput(output,templateOutput)
                templateOutput["complexdata"] = 1
            else:
                templateOutput = self._lineageBBoxOutput(output,templateOutput)
                templateOutput["bboxdata"] = 1   
        self._templateProcessor.set("Outputdefinitions",templateOutputs)

    def _lineageLiteralOutput(self, output, literalOutput):
        
        if len(output.uoms):
                literalOutput["uom"] = output.uoms[0]
        return literalOutput

    def _lineageComplexOutput(self, output, complexOutput):
        
         #Checks for the correct output and logs 
        self.checkMimeTypeOutput(output)
        complexOutput["mimetype"] = output.format["mimetype"]
        complexOutput["encoding"] = output.format["encoding"]
        complexOutput["schema"] = output.format["schema"]
        return complexOutput

    def _lineageBBoxOutput(self, output, bboxOutput):
        
        bboxOutput["bboxdata"] = 1
        bboxOutput["crs"] = output.crs
        bboxOutput["dimensions"] = output.dimensions

        return bboxOutput
    
    def processOutputs(self, outputsRequested):
        """Fill <ProcessOutputs> part in the output XML document
        This method is called if, self.status == ProcessSucceeded
        """
        templateOutputs = []
        
        for identifier in outputsRequested:
        #for identifier in self.process.outputs.keys():
            try:
                templateOutput = {}
                output = self._process.outputs[identifier]

                templateOutput["identifier"] = output.identifier
                templateOutput["title"] = self._process.i18n(output.title)
                templateOutput["abstract"] = self._process.i18n(output.abstract)
                templateOutput["metadata"] = output.metadata

                # Reference
                if output.asReference:
                    templateOutput = self._asReferenceOutput(templateOutput, output)
                # Data
                else:
                    templateOutput["reference"] = 0
                    if output.type == "LiteralValue":
                        templateOutput = self._literalOutput(output,templateOutput)
       
                    elif output.type == "ComplexValue":
                            templateOutput = self._complexOutput(output,templateOutput)
                    elif output.type == "BoundingBoxValue":
                        templateOutput = self._bboxOutput(output,templateOutput)

                templateOutputs.append(templateOutput);

            except pywps.WPSException,e:
                #In case we have a specific WPS exception e.g incorrect mimeType etc
                traceback.print_exc(file=pywps.logFile)
                self.promoteStatus(self.failed,statusMessage=e.value,exceptioncode=e.code, locator=e.locator)

            except Exception,e:
                self.cleanEnv()
                traceback.print_exc(file=pywps.logFile)
                raise pywps.NoApplicableCode(
                        "Process executed. Failed to build final response for output [%s]: %s" % (identifier,e))
        self._templateProcessor.set("Outputs",templateOutputs)

    def _literalOutput(self, output, literalOutput):

        literalOutput["uom"] = output.uom
        literalOutput["dataType"]= util.getDataTypeReference(output)["type"]
        literalOutput["literaldata"] = str(output.value)

        return literalOutput

    def _complexOutput(self, output, complexOutput):
        
        #Checks for the correct output and logs 
        self.checkMimeTypeOutput(output)
       
        complexOutput["mimetype"] = output.format["mimetype"]
        complexOutput["encoding"] = output.format["encoding"]
        complexOutput["schema"] = output.format["schema"]
       
        if output.format["mimetype"] is not None:
        # CDATA section in output
            #attention to application/xml
            if output.format["mimetype"].find("text") < 0 and output.format["mimetype"].find("xml")<0:
            #complexOutput["cdata"] = 1
                tmpoutputfile = tempfile.mkstemp("", "output", config.getConfigValue("server", "tempPath"))[1]
                #os.rename(output.value, output.value+".binary")
                base64.encode(open(output.value,'r'), open(tmpoutputfile,"w"))
                # set output value
                complexOutput["complexdata"] = open(tmpoutputfile,"r").read()
                os.remove(tmpoutputfile)
            else:
                fobj = open(output.value,"r")
                complexOutput["complexdata"] = fobj.read()
                fobj.close()

        # remove <?xml version= ... part from beginning of some xml
        # documents
        #Better <?xml search due to problems with \n
        if output.format["mimetype"] is not None:
            if output.format["mimetype"].find("xml") > -1:
                beginXMLidx=complexOutput["complexdata"].find("?>")
                #All <?xml..?> will be beginXMLidx + 2 
                
                #beginXml = complexOutput["complexdata"].split("\n")[0]
                if beginXMLidx > -1:
                    complexOutput["complexdata"] = complexOutput["complexdata"].replace(complexOutput["complexdata"][:(beginXMLidx+2)],"")

        return complexOutput

    def _bboxOutput(self, output, bboxOutput):
        bboxOutput["bboxdata"] = 1
        bboxOutput["crs"] = output.crss[0]
        bboxOutput["dimensions"] = output.dimensions
        # FIXME ve ASSUME, the coordinates are 2 dimensional
        bboxOutput["minx"] = output.value[0][0]
        bboxOutput["miny"] = output.value[0][1]
        bboxOutput["maxx"] = output.value[1][0]
        bboxOutput["maxy"] = output.value[1][1]
        return bboxOutput

    def _storeFileOnFTPServer(self, filePath, fileName, ftpURL, ftpPort,ftpLogin, ftpPasswd):
        """The method sends a file located at filePath to a FTP server with url ftpURL using ftplogin and ftppasswd as authentification.
            The vairiable fileName is the name of the file on the ftp server.
        """
       
        ftp =  pywps.Ftp.FTP(ftpURL, ftpPort)
        ftp.login(ftpLogin, ftpPasswd)
        file = open(filePath, "r")
        ftp.storbinary("STOR " + fileName, file)
        ftp.quit()
        file.close()


    def _asReferenceOutput(self,templateOutput, output):
        outputPath = config.getConfigValue("server","outputPath")
        # As default we suppose local file output
        outputType = "file"
        # Check if ftp or file storage is set in the configfile
        if string.find(outputPath.lower(), "ftp://", 0, 6) == 0:
            outputType = "ftp"
 
        # search for ftp identifier in string in outputPath and get the ftp login and password
        # TODO: Check if login or password are set, in case they are empty, anonymous is 
        # used as default
        if outputType == "ftp":
            try:
                ftpLogin = config.getConfigValue("server","ftplogin")
                ftpPasswd= config.getConfigValue("server","ftppasswd")
                try:
                    ftpPort=config.getConfigValue("server","ftpport")
                except:
                    ftpPort=21    
            except Exception, e:
                traceback.print_exc(file=pywps.logFile)
                self.cleanEnv()
                raise pywps.NoApplicableCode("FTP error: " +  e.__str__())
                
            ftpURL= outputPath[6:]

            # copy the file to output directory or send it to an ftp server
            # literal value
        #str: BoundingBoxValue
        #ATTENTION to the FTP code
        if output.type == "LiteralValue" or output.type== "BoundingBoxValue":
                #if BounfingBoxValue we'll apply the Execute_Data_Outputs.tml
                if output.type=="BoundingBoxValue":
                    bboxTemplateFileOut = os.path.join(os.path.split(self.templateFile)[0],"inc","Execute_Data_Outputs.tmpl")
                    bboxTemplateProcessor = TemplateProcessor(bboxTemplateFileOut,compile=True)
                    #Call private method to generate a proper dictionary
                    bboxOutput=self._bboxOutput(output,bboxOutput={})
                    [bboxTemplateProcessor.set(key, value) for (key,value) in bboxOutput.items()]
                    #No prettyprint to avoid problem with re
                    bboxXMLOut=bboxTemplateProcessor.__str__().replace("  ","").replace("\n","")
                    #The template will generete bboxXML wrapped in the data tag
                    try:
                        output.value=re.findall(r'<wps:Data>(.*?)</wps:Data>', bboxXMLOut)[0]
                    except Exception,e:
                        #log the error and continue as simple string
                        logging.debug("Problems generating the BBOX XML content asReference")
                        traceback.print_exc(file=pywps.logFile)
                if outputType == "ftp":
                    
                    tmpFileName = "%s-%s" % (output.identifier,self.wps.UUID)
                    f = open(tmpFileName,"w")
                    f.write(str(output.value))
                    f.close()
                    self._storeFileOnFTPServer(tmpFileName, tmpFileName,ftpURL, ftpPort, ftpLogin, ftpPasswd)
                    templateOutput["reference"] = escape(config.getConfigValue("server","outputPath")+"/" +tmpFileName)
                else:
                    tmpFileName = os.path.join(os.path.join(config.getConfigValue("server","outputPath")),"%s-%s" % (output.identifier,self.wps.UUID))
                    f = open(tmpFileName,"w")
                    f.write(str(output.value))
                    f.close()
                    templateOutput["reference"] = escape(config.getConfigValue("server","outputUrl")+"/" +os.path.basename(tmpFileName))
                
            # complex value
        else:
                outSuffix = os.path.splitext(os.path.basename(output.value))[1]
                #recall that splittext already includes .
                if outputType == "ftp":
                    tmpFileName="%s-%s%s" % (output.identifier,self.wps.UUID,outSuffix)
                else:
                    tmpFileName=os.path.join(os.path.join(config.getConfigValue("server","outputPath")),"%s-%s%s" % (output.identifier,self.wps.UUID,outSuffix))

                
                outFile = tmpFileName
                outName = os.path.basename(tmpFileName)
                if outputType == "ftp":
                    self._storeFileOnFTPServer(os.path.abspath(output.value), outName + outSuffix, ftpURL, ftpPort,ftpLogin, ftpPasswd)
                    #data sent to FTP and stored in the local output
                    COPY(os.path.abspath(output.value), outFile)
                elif not self._samefile(output.value,outFile):
                    COPY(os.path.abspath(output.value), outFile)
                
                #If ftp then the path to file is the outputpath otherwise it has to be the outputURL
                if outputType == "ftp":
                    templateOutput["reference"] = escape(config.getConfigValue("server","outputPath")+"/"+outName)
                else:
                    templateOutput["reference"] = escape(config.getConfigValue("server","outputUrl")+"/"+outName)    
                
                    output.value = outFile

                # mapscript supported and the mapserver should be used for this
                # output
                # redefine the output 
                
                #Mapserver needs the format information, therefore checkMimeType has to be called before
                self.checkMimeTypeOutput(output)
                
#                if self.umn and output.useMapscript:
#                    owsreference = self.umn.getReference(output)
#                    self.umn.save()
#                    if owsreference:
#                        templateOutput["reference"] = escape(owsreference)
                if self._mapserver:
                    owsreference = self._mapserver.save(output)
                    if owsreference:
                        templateOutput["reference"] = escape(owsreference)

                
                templateOutput["mimetype"] = output.format["mimetype"]
                templateOutput["schema"] = output.format["schema"]
                templateOutput["encoding"]=output.format["encoding"]
      

        return templateOutput

    def _samefile(self, src, dst):
        # Macintosh, Unix.
        if hasattr(os.path,'samefile'):
            try:
                return os.path.samefile(src, dst)
            except OSError:
                return False

        # All other platforms: check for same pathname.
        return (os.path.normcase(os.path.abspath(src)) ==
                os.path.normcase(os.path.abspath(dst)))

    def checkMimeTypeOutput(self,output):
            """
        Checks the complexData output to determine if the mimeType is correct.
        if mimeType is not in the list defined by the user then it will log it as an error, no further action will be taken
        Mainly used by: _asReferenceOutput,_complexOutput,_lineageComplexOutput,_lineageComplexReference
        Note: checkMimeTypeIn will set the output's format from the first time, if the user doesnt define an outputmimetype,
        we'll use the first one in the list (set by CheckMimeTypeIn), the mimeType will then be validate using ligmagic 
            """
            ######## TESTING CODE #############
            #mimeType=output.ms.file(output.value).split(';')[0]
            #if (output.format["mimetype"] is None) or (output.format["mimetype"]==""):
            #    output.format["mimetype"]=mimeType
            #    logging.debug("Since there is absolutely no mimeType information for %s, using libmagic mimeType %s " % (output.identifier,mimeType))
            #else:
            #    #check if output.format is in output.formats
            #    if output.format["mimetype"] in [item["mimeType"] for item in output.formats]:
                    #things are ok, copy all the contet to output.format
            #        output.format=[item for item in output.formats if item["mimeType"]==output.format["mimetype"]][0]
            #        output.format["mimetype"]=output.format["mimeType"]
            #        del output.format["mimeType"]
            #    else:
            #         logging.debug("ComplexOut %s has libMagic mimeType: %s but its format is %s (not in output list)" % (output.identifier,mimeType,output.format["mimetype"]))
            #         raise pywps.InvalidParameterValue(output.identifier)
     
            #return
            try: # problem with exceptions ?!
                mimeType=output.ms.file(output.value).split(';')[0]
                if (output.format["mimetype"] is None) or (output.format["mimetype"]==""):
                    output.format["mimetype"]=mimeType
                    logging.debug("Since there is absolutely no mimeType information for %s, using libmagic mimeType %s " % (output.identifier,mimeType))
                else:
                    if (mimeType.lower()!=output.format["mimetype"].lower()):
                        logging.debug("ComplexOut %s has libMagic mimeType: %s but its format is %s" % (output.identifier,mimeType,output.format["mimetype"]))
            except:
                pass
            
    def setRawData(self):
        """Sets response and contentType 
        """

        output = self.process.outputs[self.rawDataOutput]
        if output.type == "LiteralValue":
            self.contentType ="text/plain"
            self.response = output.value

        elif output.type == "ComplexValue":

            #self.checkMimeTypeIn(output)
             # copy the file to safe place
            outName = os.path.basename(output.value)
            outSuffix = os.path.splitext(outName)[1]
            tmp = tempfile.mkstemp(suffix=outSuffix, prefix="%s-%s" % (output.identifier,self.pid),dir=os.path.join(config.getConfigValue("server","outputPath")))
            outFile = tmp[1]

            if not self._samefile(output.value,outFile):
                COPY(os.path.abspath(output.value), outFile)

            #check 
            self.contentType = output.format["mimetype"]
            self.response = open(outFile,"rb")
            
    def promoteStatus(self,status, statusMessage=0, percent=0,
                    exceptioncode=0, locator=0, output=None):
        """Sets status of currently performed Execute request

        :param status:  name of the status
        :param statusMessage: message, which should appear in output xml file
        :param percent: percent done message
        :param exceptioncode: eventually exception
        :param locator: where the problem occurred
        """
        self.statusTime = time.localtime()
        self._templateProcessor.set("statustime", time.strftime('%Y-%m-%dT%H:%M:%SZ', self.statusTime))

        # init value
        self._templateProcessor.set("processstarted",0)
        self._templateProcessor.set("processsucceeded",0)
        self._templateProcessor.set("processpaused",0)
        self._templateProcessor.set("processfailed",0)
        self._templateProcessor.set("processaccepted",0)
        
        # 
        if not statusMessage:
            statusMessage = 'No msg'
            
        if status == accepted:
            self._templateProcessor.set("processaccepted",
                    statusMessage)

        elif status == started:
            self._templateProcessor.set("processstarted", statusMessage)
            self._templateProcessor.set("percentcompleted", percent)

        elif status == succeeded:
            self._process.status.set(msg=statusMessage, percentDone=100, propagate=False)
            self._templateProcessor.set("percentcompleted", percent)
            self._templateProcessor.set("processsucceeded", statusMessage)

        elif status == paused:
            self._templateProcessor.set("processpaused", statusMessage)
            self._templateProcessor.set("percentcompleted", percent)

        elif status == failed:
            self._templateProcessor.set("processfailed", 1)
            if statusMessage:
                self._templateProcessor.set("exceptiontext", statusMessage)
            self._templateProcessor.set("exceptioncode", exceptioncode)
            if locator:
                self._templateProcessor.set("locator", locator)

        if status == started:
            logging.info("Status [%s][%.1f]: %s" %\
                    (status,float(percent), statusMessage))
        else:
            logging.info("Status [%s]: %s" % (status, statusMessage))
        