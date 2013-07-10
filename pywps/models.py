import os, logging, exceptions

from django.conf import settings
from django.db import models
from django.conf import settings
from django.db.models.signals import post_syncdb, post_delete

from pywps.constant import *
from pywps.Process import WPSProcess

logger = logging.getLogger(__file__)

STATUS = ('INITIALLING', 'INITIALED', 'STARTING', 'EXECUTING', 'STOPPING', 'STOPPED', 'RESTARTING', 'CANCELLING', 'CANCELED', 'FAILED', 'SUCCESSED', )
JOBTOWPSSTATUS = {'INITIALLING':'processpaused', 'INITIALED':'processaccepted', 'STARTING':'processaccepted', 'EXECUTING':'processstarted',
                  'STOPPING':'processstarted', 'STOPPED':'processpaused', 'RESTARTING':'processpaused', 'CANCELLING':'processstarted', 'CANCELED':'processfailed', 
                  'FAILED':'processfailed', 'SUCCESSED':'processsucceeded', }

class TopicCategory(models.Model):
    name = models.CharField(max_length=50)
    slug = models.SlugField()
    description = models.TextField(blank=True)

    def __unicode__(self):
        return u"{0}".format(self.name)

    class Meta:
        ordering = ("name",)
        
        
class Meta(models.Model):
    """
    base metadata struction of OGC Web_Services_Common_Standard
    """
    title = models.CharField(max_length = 50, null = False, blank = False)
    link = models.URLField()
    
    def __unicode__(self):
        return self.title
    
    class Meta:
        unique_together = ('title', 'link',)

class Format(models.Model):
    mimeType = models.CharField(max_length=20, choices = RASTER_MIMETYPES_LIST+VECTOR_MIMETYPES_LIST, null=False, blank=False)
    encoding = models.CharField(max_length=20, blank=True, choices = [('','UTF-8'),], help_text='Reference to default encoding for process input or output')
    schema = models.CharField(max_length=50, blank = True, choices = [('','')]+VECTOR_SCHEMA_LIST, help_text = 'Reference to default XML Schema Document for process input or output')
    
    def __unicode__(self):
        return '{0}-{1}-{2}'.format(self.mimeType, self.encoding, self.schema)
    
    class Meta:
        unique_together = ('mimeType', 'encoding', 'schema', )
        
    def getFormat(self):
        """
        get format with dict structure
        """  
        ft = {'mimeType':self.mimeType}
        if self.encoding:
            ft['encoding'] = self.encoding
        if self.schema:
            ft['shema'] = self.schema
        
        return ft

class ValueReference(models.Model):
    """
    References an externally defined finite set of values and ranges for this input 
    """
    reference = models.URLField(help_text = 'URL from which this set of ranges and values can be retrieved ', null=True, blank=True)
    valuesForm = models.URLField(help_text = 'Reference to a description of the mimetype, encoding, and schema'+
                                 'used for this set of values and ranges', null=True, blank=True)  
    def __unicode__(self):
        return self.reference

class ProcessBase(models.Model):
    identifier = models.CharField(max_length=20, null=False, blank=False)
    title = models.CharField(max_length=200, null = False, blank=False)
    abstract = models.TextField(null=True, blank = True)
    Metadata = models.ManyToManyField(Meta, null=True, blank = True)
    
    def __unicode__(self):
        return self.identifier
    
    def delete_recursive(self, using=None, exclude = ()):
        """
        this delete method will delete all records in manytomany fields
        
        @param exclude: the manytomany fields name that which records needn't be deleted
        """
        # disassociate the relation of manytomany field to this process and delete them
        for _m2m in self._meta.many_to_many:
            if _m2m.name in exclude:
                continue
            _f = self.__getattribute__(_m2m.name)
            for _r in _f.all():
                if hasattr(_r, 'delete_recursive'):
                    _r.delete_recursive()
                else:
                    if _r._meta.many_to_many:
                        logger.warning("this fiels {0} have manytomany fiels {1} but not be "+
                                       "deleted recursive, and some redundancy data will be in db", 
                                       str(_r), str(_r._meta.many_to_many))
                    _r.delete()
            _f.clear()
        ProcessBase.delete(self, using=using)
    
    def getMetadata(self):
        """
        list of metadata with following format:
        FORMAT:
                [
                    {
                     "title": "Title",
                     "href": "http://bnhelp.cz/metadata/micka_main.php?ak=detail&uuid=32e80880-c3b0-11dc-8641-873e117140a9",
                     ... : ...
                     }
                ]
        """
        meta = []
        for m in self.Metadata.all():
            meta.append( {'title':m.title, 'href':m.link})
        
        return meta

    def getValueinDict(self):
        """
        get the field of this record in dict 
        
        @return: 
        {
            "identifier":
            "title":
            "abstract":
            "metadata":
        }
        """
        return {'identifier':self.identifier, 'title':self.title, 'abstract':self.abstract, 
             'metadata':self.getMetadata()}
    
class Input(ProcessBase):
    """
    defaultValue: the value format will be different with dataType changed
    """
    minOccurs = models.IntegerField(null=False, blank=False, default = 1, help_text = 'Minimum number of times that values for this parameter are required')
    maxOccurs = models.IntegerField(null = False, blank = False, default = 1, help_text = 'Maximum number of times that this parameter may be present')
    
    def getValueinDict(self):
        """
        @return: 
        {
            "identifier":
            "title":
            "abstract":
            "metadata":
            "minOccurs":
            "maxOccurs":
        }
        """
        v = super(Input,self).getValueinDict()
        v['minOccurs'] = self.minOccurs
        v['maxOccurs'] = self.maxOccurs
        
        return v

class ComplexData(Input):
    Default = models.ForeignKey(Format, null=False, blank=False, related_name = 'Default')
    Supported = models.ManyToManyField(Format, null=False, blank=False, related_name = 'Supported')
    maximumMegabytes = models.IntegerField(default = 1000, help_text='The maximum file size, in megabytes, of this input.'+
                                           ' If the input exceeds this size, the server will return an error' +
                                           ' instead of processing the inputs. ')
    
    def delete_recursive(self, using=None):
        Input.delete_recursive(self, using=using, exclude=('Supported',))
    
    def getDefaultFormat(self):
        return Default.getFormat()
    
    def getSupportedFormat(self):
        ft = []
        for f in self.Supported.all():
            ft.append(f.getFormat())
            
        return ft
    def getInputValueinDict(self):
        return None
     
    def getOutpuValueinDict(self):
        v = Input.getValueinDict(self)
        del(v['minOccurs'])
        del(v['maxOccurs'])
        v['formats'] = self.getSupportedFormat()
        
        return v

class LiteralDataOutput(ProcessBase):
    DataType = models.CharField(max_length = 10, choices = LITERALDATATYPE, null = True, blank = True)
    UOM_Default = models.CharField(max_length = 10, choices = UOM, blank=True, null=True)
    UOM_Supported = models.TextField(blank=True, null=True)
    
    def getUOMSupported(self):
        if self.UOM_Supported:
            return UOM_Supported.split(';')
        else:
            return [] 
        
    def getDataType(self):
        return TYPE_MAP[self.DataType]
    
class LiteralDataInput(Input):
    DataType = models.CharField(max_length = 10, choices = LITERALDATATYPE)
    DefaultValue = models.CharField(max_length = 50, null=True, blank = True)
    UOM_Default = models.CharField(max_length = 10, choices = UOM)
    UOM_Supported = models.TextField(null=True, blank = True)
    ValueReference = models.ForeignKey(ValueReference, null=True, blank=True)
    AllowedValues = models.TextField(null=True, blank = True)
    
    def getUOMSupported(self):
        if self.UOM_Supported:
            return self.UOM_Supported.split(';')
        else:
            return []
    
    def getLiteralValueChoice(self):
        """
        list or tulple that the values is choiced will be return , if the value is ('*'), then
        the input value will be any value
        """
        if self.AllowedValues:
            return self.AllowedValues.split(';')
        elif self.ValueReference:
            return (self.ValueReference.reference, self.ValueReference.valuesForm)
        else:
            return ('*')
        
    def getDataType(self):
        return TYPE_MAP[self.DataType]
    
    def getDefaultValue(self):
        if self.DefaultValue:
            return self.getDataType()(self.DefaultValue)
        else:
            return None 
    
class BoundingBoxData(Input):
    pass
 
class Process(ProcessBase):
    """
    process model
    """
    processVersion = models.CharField(max_length=10, null=False)
    Profile = models.CharField(max_length = 50, help_text = 'URN type, eg. OGC:WPS:somename')
    WSDL = models.URLField(help_text = 'Location of a WSDL document that describes this process.')
    storeSupported = models.BooleanField(default=False, help_text = '')
    statusSupported = models.BooleanField(default=False, help_text = 'ndicates if Execute operation response can be returned quickly withstatus information')
    
    # input
    ComplexDataInput = models.ManyToManyField(ComplexData, null = True, blank = True, verbose_name = 'complexdata inputs',related_name='ComplexDataInput_set')
    LiteralDataInput = models.ManyToManyField(LiteralDataInput, null = True, blank = True, related_name='LiteralDataInput_set')
    BoundingBoxDataInput = models.ManyToManyField(BoundingBoxData, null=True, blank = True, related_name='BoundingBoxDataInput_set')
    
    # output
    ComplexDataOutput = models.ManyToManyField(ComplexData, null=True, blank = True, related_name='ComplexDataOutput_set')
    LiteralDataOutput = models.ManyToManyField(LiteralDataOutput, null=True,blank = True, related_name='LiteralDataOutput_set')
    BoundingBoxDataOutput = models.ManyToManyField(BoundingBoxData, null=True, blank = True, related_name='BoundingBoxDataOutput_set')
    
    # other information wasn't defined in OGC WPS specification
    processType = models.CharField(max_length = 100, choices = PROCESS_TYPE_LIST)
    created_time = models.DateField(auto_now_add=True)
    recent_changed_time = models.DateField(auto_now=True)
    topiccategory = models.ForeignKey(TopicCategory)
    cmd = models.CharField(max_length=200)
    
    def getProcessClass(self):
        prsClass = None
        for cls in PROCESS_TYPE_LIST:
            if cls[0] == self.processType:
                relative_path = cls[0].split('.')
                mdClass = __import__('.'.join(relative_path[:-1]), fromlist=('.'.join(relative_path[:-1])) )
                prsClass = mdClass.__getattribute__(relative_path[-1])
                break
        
        assert prsClass
        
        logging.info('The process class is: {0}'.format(str(prsClass)))        
        return prsClass
    
    def getProcessObject(self):
        wpsprs = WPSProcess(statusSupported=self.statusSupported, storeSupported=self.storeSupported,  
                          version=self.processVersion, jobcls = self.getProcessClass(), **self.getValueinDict())
        wpsprs.model = self
        
        # add inputs
        for input in self.ComplexDataInput.all():
            wpsprs.addComplexInput(formats = input.getSupportedFormat(),maxmegabites = input.maximumMegabytes, 
                                   **input.getValueinDict())
            
        for input in self.LiteralDataInput.all():
            v = input.getValueinDict()
            if input.getUOMSupported():
                v['uoms'] = input.getUOMSupported()
            if input.getDefaultValue():
                v['default'] = input.getDefaultValue()
                
            wpsprs.addLiteralInput(allowedValues = input.getLiteralValueChoice(),
                                   type = input.getDataType(),
                                   **v
                                   )
            
        for input in self.BoundingBoxDataInput.all():
            wpsprs.addBBoxInput(**input.getValueinDict())
            
        # add outputs
        for output in self.ComplexDataOutput.all():
            wpsprs.addComplexOutput(**output.getOutpuValueinDict())
            
        for output in self.LiteralDataOutput.all():
            v = output.getValueinDict()
            if output.getUOMSupported():
                v['uoms'] = output.getUOMSupported()
                
            wpsprs.addLiteralOutput(type = output.getDataType(),
                                    **v)
            
        for output in self.BoundingBoxDataOutput.all():
            wpsprs.addBBoxOutput(**input.getValueinDict())
            
        return wpsprs
    
class Jobs(models.Model):
    """
    jobs model, 
    """
    create_time = models.DateField(auto_now_add=True)
    execution_time = models.DateTimeField(null=True)
    update_time = models.DateField(auto_now=True)
    request_method = models.CharField(max_length=15, choices=(('REQUEST_GET','get'), ('REQUEST_POST','post'),))
    request = models.TextField()
    response = models.TextField(null=True)
    stdout = models.TextField(null=True, blank=True)
    stderr = models.TextField(null=True, blank=True)
    traceback = models.TextField(null=True, blank=True)
    status = models.CharField(max_length=15, choices=((statu, str.lower(statu)) for statu in STATUS ))
    interrupt = models.BooleanField( help_text="if can be interrupt of this job.It's true and false for async and sync request respectively") 
    statusLocation = models.FilePathField(null=True, help_text="file that storing status information of execute with async request. So, it's will be Null with sync request")
    
    process = models.ForeignKey(Process)
    cmd = models.TextField(null=True, help_text = 'executabled string used by Popen')
    pickled_string = models.TextField(null=True, help_text='pickle Popen instance to string and save')
    
def format_initial(instance, sender, **kwargs):
    for mimetype in RASTER_MIMETYPES:
        Format.objects.create(mimeType=mimetype)
        
    for ft in VECTOR_MIMETYPES:
        Format.objects.create(mimeType=ft.get('MIMETYPE',''), encoding=ft.get('ENCODING',''), SCHEMA=ft.get('SCHEMA',''))
        
def input_delete_of_process(instance, sender, **kwargs):
    del_attr = [instance.ComplexDataInput, instance.LiteralDataInput, instance.BoundingBoxDataInput,
                instance.ComplexDataOutput, instance.LiteralDataOutput, instance.BoundingBoxDataOutput]
    
    for attr in del_attr:
        if attr:
            for a in attr.all():
                a.delete()
    
def metadata_delete_of_processbase(instance, sender, **kwargs):
    if instance.Metadata:
        for mt in instance.Metadata.all():
            mt.delete()
    
if 'pywps' in settings.INSTALLED_APPS:
    post_syncdb.connect(receiver = format_initial, sender = Format)
    post_delete.connect(receiver = input_delete_of_process, sender = Process)
    post_delete.connect(receiver = metadata_delete_of_processbase, sender=ProcessBase)