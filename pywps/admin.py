from django.db import models
import autocomplete_light
from django.contrib import admin
from django.forms.widgets import SelectMultiple
from pywps.models import *

#_fieldsets = [
#            (None, {'fields':(('identifier','title'), 'abstract', 'Metadata',('minOccurs','maxOccurs'),),'classes':('collapse',),} ),
#            ]
#
class MetaInputInline(admin.StackedInline):
    model = Meta
    extra = 1
    
class LiteralDataInputInline(admin.StackedInline):
    model = LiteralDataInput
    verbose_name = 'LiteralData Inputs'
    extra = 1
    
class ComplexDataInputInline(admin.StackedInline): 
    model = ComplexData
    verbose_name = 'ComplexData Inputs'
    fieldsets = [
                 (None, {'fields':(('identifier','title'), 'abstract', 'Metadata',('minOccurs','maxOccurs'),('Default'), ('Supported', )),
                         'classes':('wide',),} ),
#                 ('inputs',{'fields':('Default', 'Supported', ),}),
                ]
    inlines = [MetaInputInline,]
    filter_horizontal = ('Supported',)
    extra = 1
    
class LiteralDataOutputInline(admin.StackedInline):
    model = LiteralDataOutput
    verbose_name = 'LiteralData Outputs'
    extra = 1
    
class ComplexDataOutputInline(admin.StackedInline):
    model = ComplexData
    verbose_name = 'ComplexData Outputs'
    exclude = ['maximumMegabytes', 'minOccurs', 'maxOccurs']
    filter_horizontal = ('Supported',)
    extra = 1
    
class ProcessAdmin(admin.ModelAdmin):
#    fields = (('identifier','processVersion'),'title', 'abstract', ('processType', 'execFile', 'cmd',),
#              ('LiteralDataInput', 'ComplexDataInput'),('LiteralDataOutput', 'ComplexDataOutput'),)
    form = autocomplete_light.modelform_factory(Process)
    fieldsets = [
                 ('Base information', {
                                       'fields':(('identifier','processVersion'),'title', 'abstract', 'topiccategory', 'cmd'),
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
    inlines = [LiteralDataInputInline, ComplexDataInputInline, LiteralDataOutputInline, ComplexDataOutputInline,]

#    formfield_overrides = {
#                           models.ManyToManyField:{'widget':SelectMultiple(attrs={'width':'10'}), 'queryset':models.query.EmptyQuerySet()},
#                           }
    
    #filter_horizontal = ('LiteralDataInput','ComplexDataInput',)
    
    list_display = ['identifier', 'processVersion']
    search_fields = ['identifier']
    
admin.site.register((Format, TopicCategory))
admin.site.register(Process, ProcessAdmin)
#admin.site.register(ComplexData, ComplexDataAdmin)