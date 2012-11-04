#!/usr/bin/env python
#-*- coding:utf-8 -*-
import os
import sys
from lxml import etree
import logging

workdir = os.path.split(__file__)[0]
pywpsPath = os.path.abspath(os.path.join(os.path.split(os.path.abspath(__file__))[0],"..",".."))
sys.path.insert(0,pywpsPath)
sys.path.append(pywpsPath)

import pywps

"set the log"
log = logging.getLogger(__file__)
log.level = logging.DEBUG

def Usage():
    return "Usage:wpstogalaxy [prsdir] [dir] [process] [disfile] \n"\
        " \tprsdir: the processes directory can used by pywps service\n" \
        " \tdir: the directory that galaxy tools configure file will be wrote to\n" \
        " \tprocess: the single process name\n" \
        " \tdisfile: the destination file that will save configure file transformed.Only used with process\n"

def TransProcess(process, file):
    """Get process describe of wps serive and transform to galaxy tools configure file"""
    
    request = "Service=WPS&Version=1.0.0&request=describeprocess&identifier={0}".format(process)
    wpsreq = pywps.Pywps(pywps.METHOD_GET)
    wpsreq.parseRequest(request)
    wpsreq.performRequest()
    
    if wpsreq.response.find("ExceptionReport") == -1:
        "transform"
        xslttree = etree.parse(os.path.join(workdir,'wpstogalaxy.xsl')).getroot()
        xmltree = etree.fromstringlist(wpsreq.response)
        trans = etree.XSLT(xslttree)
        resxml = trans(xmltree)
        "write result"
        f = open(file,'w')
        f.write(str(resxml))
        f.close()
        return
    else:
        "error of service"
        return wpsreq.response

def TransProcesses(dir):
    """Get all the processes' describetion and transform to galaxy tools configure file"""
    
    listf = os.path.join(dir,"processeslist.txt")
    
    if not os.path.exists(dir):
        os.mkdir(dir)
        os.mknod(listf)
        
    "create log file and set to logging system"
    log.addHandler(logging.FileHandler(os.path.join(dir,"process.log"),'w'))
    
    request = "Service=WPS&Version=1.0.0&request=GetCapabilities"
    wpsreq = pywps.Pywps(pywps.METHOD_GET)
    wpsreq.parseRequest(request)
    wpsreq.performRequest()
    
    if wpsreq.response.find("ExceptionReport") != -1:
        log.error(wpsreq.response)
        return 
    
    listf = open(listf, 'w')
    capabtree = etree.fromstring(wpsreq.response)
    for elem in capabtree.xpath("//*[local-name()='Process']"):
        prs = elem.xpath("./*[local-name()='Identifier']")[0].text
        res = TransProcess(prs, os.path.join(dir, prs+'.xml'))
        if res != None:
            log.info("Some wrong when transform, detail in {0} file ".format(os.path.join(dir, prs+'.xml')))
            open(os.path.join(dir, prs), 'w').write(res)
        else:
            listf.write(prs+".xml\n")
            log.info("Successed transform process:{0}".format(prs))
    listf.close()
        
def __main__(argv):
    """argv = sys.argv"""
    isformat = False
    for index, param in enumerate(argv[1:]):
        name, value = param.split('=')
        if name == "prsdir":
            os.environ.update({'PYWPS_PROCESSES':os.path.abspath(value)})
        elif name == "dir":
            TransProcesses(value)
            isformat = True
        elif name == "process":
            for p in argv:
                fn, fv = param.split('=')
                if name == "disfile":
                    res = TransProcess(value, fv)
                    if res != None:
                        open(fv,'w').write(res)
                        isformat = True
    
    "if the input format is right"
    if isformat == False:
        return Usage()
        
if __name__=="__main__":
    try:
        res = __main__(sys.argv)
#    except ValueError,e:
#        print Usage()
    except BaseException,e:
        print e
    else:    
        if res != None:
            print Usage()
                
