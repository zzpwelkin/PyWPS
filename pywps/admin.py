from django.db import models
from django.contrib import admin
from django.forms.widgets import SelectMultiple
from pywps.models import *

#_fieldsets = [
#            (None, {'fields':(('identifier','title'), 'abstract', 'Metadata',('minOccurs','maxOccurs'),),'classes':('collapse',),} ),
#            ]
#
#class ComplexDataInput(admin.StackedInline): 
#    model = ComplexData
#    fieldsets = [
#                 (None, {'fields':(('identifier','title'), 'abstract', 'Metadata',('minOccurs','maxOccurs'),),
#                         'classes':('wide',),} ),
#                 ('inputs',{'fields':('Default', 'Supported', ),}),
#                ]
##    _fieldsets.append(('inputs',{'fields':('Default', 'Supported', ),
##                    }))
#    extra = 1
#    
#class ComplexDataOutputInline(admin.StackedInline):
#    model = ComplexData
#    extra = 1
#    exclude = ['maximumMegabytes', 'minOccurs', 'maxOccurs']

class ComplexDataAdmin(admin.ModelAdmin):
    filter_horizontal = ('Supported',)
    
class ProcessAdmin(admin.ModelAdmin):
#    fields = (('identifier','processVersion'),'title', 'abstract', ('processType', 'execFile', 'cmd',),
#              ('LiteralDataInput', 'ComplexDataInput'),('LiteralDataOutput', 'ComplexDataOutput'),)
    fieldsets = [
                 ('Base information', {
                                       'fields':(('identifier','processVersion'),'title', 'abstract'),
                                       'description':'add the base information of this process',
                                       } 
                  ),
                 ('inputs choice', {
                                    'fields':('LiteralDataInput','ComplexDataInput',),
                                    'classes':('collapse',),
                                    'description':'LiteralData or ComplexData or BBoundingData',
                                    },
                   ),
                 ('outputs choice', {
                                    'fields':('LiteralDataOutput','ComplexDataOutput',),
                                    'classes':('collapse',),
                                    'description':'LiteralData or ComplexData or BBoundingData',
                                    },
                   ),
                 ]
#    inlines = [ComplexDataInput,]

    formfield_overrides = {
                           models.ManyToManyField:{'widget':SelectMultiple},
                           }
    
    filter_horizontal = ('LiteralDataInput','ComplexDataInput',)
    
    list_display = ['identifier', 'processVersion']
    search_fields = ['identifier']
    
admin.site.register((Format, Meta, LiteralDataInput, LiteralDataOutput, TopicCategory))
admin.site.register(Process, ProcessAdmin)
admin.site.register(ComplexData, ComplexDataAdmin)