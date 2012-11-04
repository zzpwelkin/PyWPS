#!/usr/bin/env python
#-*- encoding:utf-8 -*-
from lxml import etree
import os

workdir = os.path.split(__file__)[0]

xslttree = etree.parse(os.path.join(workdir,'wpstogalaxy.xsl')).getroot()

xmltree = etree.parse(os.path.join(workdir,'maxlik_test.xml'))

trans = etree.XSLT(xslttree)
resxml = trans(xmltree)

print 'Result: '+str(resxml)
print 'Log_err: '+str(trans.error_log)