#!/usr/bin/env python
#-*- encoding:utf-8 -*-
import sys
from os import environ,path
import pywps
from lxml import etree
import logging

log = logging.getLogger( __name__ )
log.addHandler(logging.StreamHandler())
log.level = logging.DEBUG

wpsnm = 'http://www.opengis.net/wps/1.0.0'
owsnm = 'http://www.opengis.net/ows/1.1'

#sys.path.append('/home/zzpwelkin/information.lib/backup/eclipse集成开发环境/eclipseCDT/plugins/org.python.pydev.debug_2.3.0.2011121518/pysrc/')
#import pydevd
#pydevd.settrace()

def Usage():
    use = __file__ + "input output[,output,...]"
    print use
    
if len(sys.argv) < 2:
    Usage()

# get the pywps_cfg file and set the enviroment variable 'PYWPS_CFG'
pywps_conf = path.join( path.split(__file__)[0], 'pywps.cfg')

if not path.exists( pywps_conf ):
    raise BaseException("Can't find pywps config file pywps.cfg in current directory!")

#log.debug("The configure file of Unable to finish jobpywps is {0}".format(pywps_conf))

environ.update({'PYWPS_CFG':pywps_conf})

wps = pywps.Pywps( pywps.METHOD_POST )

wps.parseRequest( open( sys.argv[1]) )

wps.performRequest()

# set the result to output file
xmltree = etree.fromstring( wps.response )

outelem = xmltree.findall( '{wps}ProcessOutputs/{wps}Output'.format(wps='{' + wpsnm + '}') )

# if get an exception set to stderr
if len(outelem) == 0:
    sys.stderr = wps.response
    raise BaseException(wps.response)

# else set the result to output file
for output in sys.argv[2:]:
    output = open( output ).read().strip('\n\t ')
    name, outfile = output.split(':')
    fs = open( outfile , 'w' )
    # get the element of output and write them to output file 
    for elem in outelem:
        if name == elem.find( '{ows}Identifier'.format(ows = '{'+ owsnm +'}')).text:
            value = ''
            ref = elem.find( '{wps}Reference'.format( wps = '{' + wpsnm + '}' ) )
            if ref != None:
                value = ref.attrib['href']
            else:
                value = elem.find('{wps}Data'.format ( wps = '{'+wpsnm+'}' ) ).getchildren()[0].text

        fs.write ( value )
        #log.info('{out} value is:{val}'.format(out=name, val=value) )

    fs.close()
