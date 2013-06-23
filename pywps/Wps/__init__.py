"""
Wps Request
-----------
"""
# Author:       Jachym Cepicky
#               http://les-ejk.cz
#               jachym at les-ejk dot cz
# Lince:
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
__all__ = ["GetCapabilities","DescribeProcess","Execute","Wsdl"]

import os, types
import xml.dom.minidom
# make sure, that the package python-htmltmpl is installed on your system!
import pywps
from pywps import config
from pywps.Exceptions import *
from pywps.Template import TemplateProcessor
from pywps import Templates
from pywps import Soap
import logging

from pywps import models

class Request:
    """WPS Request performing, and response formating

    :param wps: instance of :class:`Pywps`
http://wiki.rsg.pml.ac.uk/pywps/Introduction
    .. attribute:: response
        
        formated response output

    .. attribute:: wps

        instance of :class:`pywps.PyWPS`

    .. attribute:: templateFile

        name of the template file (based on WPS version and request type)

    .. attribute:: processDir

        temporary created directory, where the process is running

    .. attribute:: templateVersionDirectory

        directory, where templates are stored (based on WPS version)
        
    .. attribute:: precompile

        indicates, if the template shuld be precompiled for later usage or
        not

    .. attribute:: stdOutClosed

        indicates, if we can write to standard output or not (usualy it is
        opend, it is closed only while the process is running in
        assynchronous mode)
        
    .. attribute:: templateProcessor

        instance of :class:`pywps.Template.TemplateProcessor`

    .. attribute:: processes

        list of instances of :`class:`pywps.Process.WPSProcess`

    .. attribute:: processSources

        list of sources of processes

    .. attribute :: contentType

        Response content type, text/xml usually
    """

    response = None # Output document
    respSize = None # Size of the ouput document
    wps = None # Parent WPS object
    templateFile = None # File with template
    processDir = None # Directory with processes
    templateVersionDirectory = None # directory with templates for specified version
    precompile = 1
    stdOutClosed = False
    templateProcessor = None
    processes = None
    processSources = None
    contentType = "application/xml"

    def __init__(self,wps,processes=None):
        """Class constructor"""
        self.wps = wps
        self.processes = processes

        self.templateVersionDirectory = self.wps.inputs["version"].replace(".","_")

        if os.name == "nt" or os.name == "java":
            self.precompile = 0

        # Templates can be stored in other directory
        templates = Templates.__path__[0]
        if os.getenv("PYWPS_TEMPLATES"):
            templates = os.path.abspath(os.getenv("PYWPS_TEMPLATES"))

        if self.wps.inputs.has_key("request"):
            if self.wps.inputs["request"] == "getcapabilities":
                self.templateFile = os.path.join(templates,
                                    self.templateVersionDirectory,
                                        "GetCapabilities.tmpl")
            elif self.wps.inputs["request"] == "describeprocess":
                self.templateFile = os.path.join(templates,
                                    self.templateVersionDirectory,
                                        "DescribeProcess.tmpl")
            elif self.wps.inputs["request"] == "execute":
                self.templateFile = os.path.join(templates,
                                    self.templateVersionDirectory,
                                        "Execute.tmpl")
        try:
            self.templateProcessor = TemplateProcessor(self.templateFile,compile=True)
        except pywps.Template.TemplateError,e:
            raise NoApplicableCode("TemplateError: %s" % repr(e))
        
    def _getProcessRecord(self, identifier, version):
        """Get single record of models.Process instance based on identifier and version"""
        if version:
            p = models.Process.objects.filter(identifier = identifier, processVersion=version)
        else:
            p = models.Process.objects.filter(identifier = identifier)
            
        if len(p) == 0:       
            raise InvalidParameterValue("Process %s not available" % identifier)
        
        return p[0]
        
    def _getAllProcess(self):
        ps = []
        for p in models.Process.objects.all():
            ps.append( p.getProcessObject() )
            
        return ps

    def checkProcess(self,identifiers):
        """check, if given identifiers are available as processes"""

        # string to [string]
        if type(identifiers) == type(""):
            identifiers = [identifiers]

        # for each process
        for prc in self.wps.inputs["identifier"]:
            psv = self.wps.inputs.get('processVersion',None)
            self._getProcessRecord(prc, psv)

    def cleanEnv(self):
        """Clean possible temporary files etc. created by this request
        type
        
        .. note:: this method is empty and should be redefined by particula
            instances
        """
        pass

    def getProcess(self,identifier, version = None):
        """Get single processes based on it's identifier and version"""

        if type(identifier) == type([]):
            identifier = identifier[0]
        
        return self._getProcessRecord(identifier, version).getProcessObject()

    def getProcesses(self,identifiers=None):
        """Get list of processes identified by list of identifiers

        :param identifiers: List of identifiers. Either list of strings, or 'all'
        :returns: list of process instances or none
        """

        if not identifiers:
            raise MissingParameterValue("Identifier")

        if type(identifiers) == types.StringType:
            if identifiers.lower() == "all":
                return self._getAllProcess()
            else:
                return self.getProcess(identifiers)
        else:
            processes = []
            for identifier in identifiers:
                if identifier.lower() == "all":
                    return self._getAllProcess()
                else:
                    processes.append(self.getProcess(identifier))

            if len(processes) == 0:
                raise InvalidParameterValue(identifier)
            else:
                return processes

    def formatMetadata(self,process):
        """Create structure suitble for template form process.metadata

        :param process: :attr:`pywps.Process`
        :returns: hash with formated metadata
        """
        
        metadata = process.metadata
        if type(metadata) == type({}):
            metadata = [metadata]

        metadatas = []
        for metad in metadata:
            metaStructure = {}

            if metad.has_key("title"):
                metaStructure["title"] = metad["title"]
            else:
                metaStructure["title"] = process.title

            if metad.has_key("href"):
                metaStructure["href"] = metad["href"]
            else:
                metaStructure["href"] = config.getConfigValue("wps","serveraddress")+\
                        "?service=WPS&amp;request=DescribeProcess&amp;version="+config.getConfigValue("wps","version")+\
                        "&amp;identifier="+ process.identifier

            metadatas.append(metaStructure)
            
        return metadatas
