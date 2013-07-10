"""
This file demonstrates writing tests using the unittest module. These will pass
when you run "manage.py test".

Replace this with more appropriate tests for your application.
"""
import unittest, os, datetime, time
from contextlib import closing
from owslib import wps
from lxml import etree

from django.test import TestCase
from django.test import Client
from django.core.urlresolvers import reverse
from pywps import util, models, Pywps, METHOD_GET, METHOD_POST
from pywps.Pywps import Pywps

testPath = os.path.join(os.path.dirname(__file__), 'wpstests')
resultsPath = os.path.join(os.path.dirname(__file__), 'wpstests', 'results_doc')
processesPath = os.path.join(os.path.dirname(__file__), 'wpstests', 'processes')
requestsPath = os.path.join(testPath, 'requests')
class RequestTest(TestCase):
    def setUp(self):
        # format
        default_ft = models.Format.objects.create(mimeType="IMAGE/TIFF")
        ######################## insert literalprocess process #####################
        # meta define
        mt = models.Meta.objects.create(title='Literal Process', link='http://zzpwelkin.com')
        # inputs
        stringInput = models.LiteralDataInput.objects.create(identifier='in_string', title ='String data in', DataType='string', minOccurs=1, maxOccurs=1)
        intInput = models.LiteralDataInput.objects.create(identifier='in_int', title='Integer data in', DataType='integer', DefaultValue='1', minOccurs=1, maxOccurs=1)        
        # outputs
        intOutput = models.LiteralDataOutput.objects.create(identifier='out_int', title='Integer data out', DataType='integer')
        stringOutput = models.LiteralDataOutput.objects.create(identifier='out_string', title ='String data out', DataType='string')        
        # process
        literalprocess = models.Process.objects.create(identifier='literalprocess', title = 'Literal process', abstract='',
                                      processVersion = '1.0', processType = 'pywps.jobs.jobs.NormalProcessJob', storeSupported=True, 
                                      topiccategory = models.TopicCategory.objects.get(slug='miscellaneous'),
                                      cmd=os.path.join(processesPath, 'literalprocess.py')+' in_int in_string out_int out_string')
        literalprocess.LiteralDataInput.add(stringInput, intInput)
        literalprocess.LiteralDataOutput.add(intOutput, stringOutput)
        literalprocess.Metadata.add(mt)
                
        ######################## insert sync raster_resize process ###################### 
        # inputs
        mt_rasterinput = models.Meta.objects.create(title='raster input', link='http://raster')
        resize_input = models.ComplexData.objects.create(identifier='resize_input', title='raster will be read', Default = default_ft, minOccurs=1, maxOccurs=1, maximumMegabytes=100)
        resize_input.Supported.add(*models.Format.objects.all())
        resize_input.Metadata.add(mt_rasterinput)
        resize_ow = models.LiteralDataInput.objects.create(identifier='resize_ow', title='width want to output', DataType='integer',  minOccurs=1, maxOccurs=1)
        resize_oh = models.LiteralDataInput.objects.create(identifier='resize_oh', title='heigth want to output', DataType='integer',  minOccurs=1, maxOccurs=1)       
        # outputs
        resize_output = models.ComplexData.objects.create(identifier='resize_output', title = 'raster will be write', Default = default_ft, minOccurs=1, maxOccurs=1, maximumMegabytes=100)
        resize_output.Supported.add(*models.Format.objects.all())       
        # process
        resizeprocess = models.Process.objects.create(identifier='raster_resize', title='raster resize', processVersion='1.0', processType='pywps.jobs.jobs.NormalProcessJob',
                                                      topiccategory=models.TopicCategory.objects.get(slug='miscellaneous'), 
                                                      cmd = os.path.join(processesPath, 'raster_resize.py') +' resize_input resize_ow resize_oh resize_output', 
                                                      )
        resizeprocess.ComplexDataInput.add(resize_input)
        resizeprocess.LiteralDataInput.add(resize_ow, resize_oh)
        resizeprocess.ComplexDataOutput.add(resize_output)
        
        ######################## insert async raster_resize process ###################### 
        # inputs
        resize_input = models.ComplexData.objects.create(identifier='resize_input', title='raster will be read', Default = default_ft, minOccurs=1, maxOccurs=1, maximumMegabytes=100)
        resize_input.Supported.add(*models.Format.objects.all())
        resize_ow = models.LiteralDataInput.objects.create(identifier='resize_ow', title='width want to output', DataType='integer',  minOccurs=1, maxOccurs=1)
        resize_oh = models.LiteralDataInput.objects.create(identifier='resize_oh', title='heigth want to output', DataType='integer',  minOccurs=1, maxOccurs=1)
        resize_waittime = models.LiteralDataInput.objects.create(identifier='resize_waittime', title='time waited for execute', DataType='integer',  minOccurs=0, maxOccurs=1)       
        # outputs
        resize_output = models.ComplexData.objects.create(identifier='resize_output', title = 'raster will be write', Default = default_ft, minOccurs=1, maxOccurs=1, maximumMegabytes=100)
        resize_output.Supported.add(*models.Format.objects.all())       
        # process        
        async_resizeprocess = models.Process.objects.create(identifier='async_raster_resize', title='raster resize', processVersion='1.0', processType='pywps.jobs.jobs.NormalProcessJob',
                                                      storeSupported=True, statusSupported = True, topiccategory=models.TopicCategory.objects.get(slug='miscellaneous'), 
                                                      cmd = os.path.join(processesPath, 'raster_resize.py') +' resize_input resize_ow resize_oh resize_output resize_waittime', 
                                                      )
        async_resizeprocess.ComplexDataInput.add(resize_input)
        async_resizeprocess.LiteralDataInput.add(resize_ow, resize_oh, resize_waittime)
        async_resizeprocess.ComplexDataOutput.add(resize_output)
        
        # the number of process
        self.process_num = 3
        
    def tearDown(self):
        for process in models.Process.objects.all():
            process.delete_recursive()

        
    def test_process_delete(self):
        """
        test if it's have delete all the records about this process
        """
        self.assertEqual(3, len(models.Process.objects.all()) )
        self.assertEqual(2, len(models.Meta.objects.all()) )
        self.assertEqual(4 , len(models.ComplexData.objects.all()) )
        self.assertEqual(7, len(models.LiteralDataInput.objects.all()) )
        self.assertEqual(2, len(models.LiteralDataOutput.objects.all()) )
        
        literalprocess = models.Process.objects.get(identifier = 'literalprocess')
        literalprocess.delete_recursive()
        self.assertEqual(1, len(models.Meta.objects.all()) )
        
        rasterresize = models.Process.objects.get(identifier = 'raster_resize')
        rasterresize.delete_recursive()
        self.assertTrue(not models.Meta.objects.all(), 'the metadata should be cleared but {0} also exits'.format(str(models.Meta.objects.all())))
            
        self.assertEqual(2 , len(models.ComplexData.objects.all()) )
        self.assertEqual(3, len(models.LiteralDataInput.objects.all()) )
        self.assertTrue(not models.LiteralDataOutput.objects.all())
        async_rasterresize = models.Process.objects.get(identifier = 'async_raster_resize')
        async_rasterresize.delete_recursive()
        
        self.assertTrue(not models.LiteralDataInput.objects.all())
        self.assertTrue(not models.ComplexData.objects.all())
        
        self.assertTrue(models.Format.objects.all())
        for f in models.Format.objects.all():
            f.delete()
        
    def test_process_notexit_exception(self):
        """
        test if exception response will be return when process not exit
        """
        request = 'service=wps&request=describeprocess&version=1.0.0&identifier=notexit'
        mywps = Pywps(METHOD_GET)
        mywps.parseRequest(request)
        
        try:
            mywps.performRequest()
        except  Exception, e:
            self.assert_(True, "The error is {0}".format(e))
        else:
            self.assert_(False, "An exception should be raised")

    def test_getcapabilities(self):
        """
        Tests GetCapabilities of WPS 
        """
        request = 'service=wps&request=getcapabilities&version=1.0.0'
        mywps = Pywps(METHOD_GET)
        mywps.parseRequest(request)
        mywps.performRequest()
        
        cap_etree = wps.WPSCapabilitiesReader().readFromString(mywps.response)
        # TODO: provider and service tests
        
        # Process tests
        process_etree = cap_etree.xpath('//wps:Process', namespaces = cap_etree.nsmap)
        
        self.assertEqual(self.process_num, len(process_etree))
        
        prs = wps.Process(process_etree[0])
        self.assertEqual('literalprocess', prs.identifier)
        self.assertEqual('1.0', prs.processVersion)
        
        # test client request
        c = Client()
        response = c.get(reverse('wps_service'),  {'service':'wps', 'version':'1.0.0', 'request':'getcapabilities', })
        self.assertEqual(mywps.response, response.content)
        
    def test_decribeprocess(self):
        """
        Tests DescribeProcess of WPS
        """
        request = 'service=wps&request=describeprocess&version=1.0.0&identifier=literalprocess'
        mywps = Pywps(METHOD_GET)
        mywps.parseRequest(request)
        mywps.performRequest()
        
        desc_etree = wps.WPSDescribeProcessReader().readFromString(mywps.response)
        # Process tests
        process_etree = desc_etree.xpath('//ProcessDescription', namespaces = desc_etree.nsmap)
        prs = wps.Process(process_etree[0])
        self.assertEquals( (True, False), (prs.storeSupported, prs.statusSupported) )
        
        # Input tests
        self.assertEqual(2, len(prs.dataInputs))
        inputs = {}
        for input in prs.dataInputs:
            inputs[input.identifier] = input
          
        self.assertEquals( ('//www.w3.org/TR/xmlschema-2/#string', '//www.w3.org/TR/xmlschema-2/#integer'), (inputs['in_string'].dataType, inputs['in_int'].dataType) )  
        self.assertEquals((1,1,0,1), (inputs['in_string'].minOccurs, inputs['in_string'].maxOccurs,inputs['in_int'].minOccurs,inputs['in_int'].maxOccurs))
            
        # Output tests
        self.assertEqual(2, len(prs.processOutputs))
        outputs = {}
        for output in prs.processOutputs:
            outputs[output.identifier] = output
        self.assertEquals( ('//www.w3.org/TR/xmlschema-2/#string', '//www.w3.org/TR/xmlschema-2/#integer'), (outputs['out_string'].dataType, outputs['out_int'].dataType) )
            
        # test client request
        c = Client()
        response = c.get(reverse('wps_service'), {'service':'wps', 'version':'1.0.0', 'request':'describeprocess','identifier':'literalprocess' })
        self.assertEqual(mywps.response, response.content)
        
    def test_literal_execute(self):
        """
        Tests Execute of WPS with literal inputs and ouputs
        """
        request = 'service=wps&version=1.0.0&request=execute&identifier=literalprocess&datainputs=[in_int=1;in_string=foo.com]'
        mywps = Pywps(METHOD_GET)
        mywps.parseRequest(request)
        mywps.performRequest()
        
        execution = wps.WPSExecution()
        execution.parseResponse(wps.WPSExecuteReader().readFromString(mywps.response))
        
        # successful assert 
        self.assert_(execution.isSucceded(), mywps.response)
        
        outputs = {}
        for ot in execution.processOutputs:
            outputs[ot.identifier] = ot
            
        self.assertEquals( (1, 'foo.com'), (outputs['out_int'].data[0], outputs['out_string'].data[0]))
        self.assertEquals( ('string', 'integer'), (outputs['out_string'].dataType, outputs['out_int'].dataType) )
        
    def test_complex_execute(self):
        """
        Tests raw raster complexdata execute
        """
        mywps = Pywps(METHOD_POST)
        
        with closing(open(os.path.join(requestsPath, 'wps_execute_request-raster_resize.xml'), 'r')) as f:
            mywps.parseRequest(f)
            
        mywps.performRequest()
                
        execution = wps.WPSExecution()
        execution.parseResponse(wps.WPSExecuteReader().readFromString(mywps.response))
        
        self.assert_(execution.isSucceded(), mywps.response)
        
        outputs = {}
        for ot in execution.processOutputs:
            outputs[ot.identifier] = ot
        
        self.assertRegexpMatches(ot.data[0], '^SUkqAA.*')
        
    def test_lineage_execute(self):
        """
        Test response document with lineage flag request
        """
        pass
        
    def test_async_complex_execute(self):
        """
        Tests async request
        """
        mywps = Pywps(METHOD_POST)
        
        with closing(open(os.path.join(requestsPath, 'wps_execute_async_request-raster_resize.xml'), 'r')) as f:
            mywps.parseRequest(f)
            
        mywps.performRequest()
                
        execution = wps.WPSExecution()
        execution.parseResponse(wps.WPSExecuteReader().readFromString(mywps.response))
        
        self.assert_(not execution.isComplete(), mywps.response)
        self.assertEqual('ProcessStarted', execution.status)
        self.assertTrue(execution.statusLocation)
        
        # waite for complete
        time.sleep(6)
        response = open(util.statusLocationUrltoFile(execution.statusLocation)).read()
        execution.parseResponse(wps.WPSExecuteReader().readFromString(response))
        
        execution2 = wps.WPSExecution()
        execution2.parseResponse(wps.WPSExecuteReader().readFromString(response))
        self.assert_(execution2.isSucceded(), response)
        
    def test_jobs_list(self):
        pass
    
    def test_job_cancel(self):
        """
        There are two scene for this test. 
        1. if a job has terminate no matter successed or failed. the response document status should be the one as previous
        2. Cancel a job , the status should be failed with cancel message
        """
        pass
    
    def test_job_stop(self):
        """
        There are two scene for this test. 
        1. Cancel a job with executing. the response document status should be paused
        2. Cancel a job with others status, the response document status should be the one as previous
        """
        pass
    
    def test_job_restart(self):
        pass
    
class RequestTestWithFlag(TestCase):
    def setUp(self):
        # format
        default_ft = models.Format.objects.create(mimeType="IMAGE/TIFF")                
        ######################## gdal_translate process ######################       
        # inputs
        resize_input = models.ComplexData.objects.create(identifier='src_dataset', title='raster will be read', Default = default_ft, minOccurs=1, maxOccurs=1, maximumMegabytes=100)
        resize_input.Supported.add(*models.Format.objects.all())
        resize_ow = models.LiteralDataInput.objects.create(identifier='ysize', title='width want to output', DataType='integer',  minOccurs=1, maxOccurs=1)
        resize_oh = models.LiteralDataInput.objects.create(identifier='xsize', title='heigth want to output', DataType='integer',  minOccurs=1, maxOccurs=1)    
        # outputs
        resize_output = models.ComplexData.objects.create(identifier='dst_dataset', title = 'raster will be write', Default = default_ft, minOccurs=1, maxOccurs=1, maximumMegabytes=100)
        resize_output.Supported.add(*models.Format.objects.all())       
        # process
        gdal_translate = models.Process.objects.create(identifier='gdal_translate', title='raster resize', processVersion='1.0', processType='pywps.jobs.jobs.NormalProcessJob',
                                                      storeSupported=True, statusSupported = True, topiccategory=models.TopicCategory.objects.get(slug='miscellaneous'), 
                                                      cmd = 'gdal_translate -outsize xsize ysize src_dataset dst_dataset', 
                                                      )
        gdal_translate.ComplexDataInput.add(resize_input)
        gdal_translate.LiteralDataInput.add(resize_ow, resize_oh)
        gdal_translate.ComplexDataOutput.add(resize_output)
        
        # the number of process
        self.process_num = 1
        
    def tearDown(self):
        gdal_translate = models.Process.objects.get(identifier='gdal_translate')
        gdal_translate.delete_recursive()
        
    def test_execute(self):
        """
        Tests raw raster complexdata execute
        """
        mywps = Pywps(METHOD_POST)
        
        with closing(open(os.path.join(requestsPath, 'wps_execute_request-gdal_translate.xml'), 'r')) as f:
            mywps.parseRequest(f)
            
        mywps.performRequest()
                
        execution = wps.WPSExecution()
        execution.parseResponse(wps.WPSExecuteReader().readFromString(mywps.response))
        
        self.assert_(execution.isSucceded(), mywps.response)
        
        outputs = {}
        for ot in execution.processOutputs:
            outputs[ot.identifier] = ot
        
        self.assertRegexpMatches(ot.data[0], '^SUkqAA.*')