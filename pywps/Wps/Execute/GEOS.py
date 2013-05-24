# Author:    zupeng zhang
#            email: zhangzupeng19871203@126.com
#
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

import os, uuid
import logging
import urllib2
import exceptions
import tempfile, zipfile
from pywps import config
from pywps.Wps.Execute.MapServer import MapServer

try:
    from geoserver.catalog import Catalog, FailedRequestError
except Exception,e:
    logging.info("gsconfig could not be loaded, geoserver not supported: %s" %e)
    
class GeoServer(MapServer):
    def __init__(self, process, sessId):
        MapServer.__init__(self, process, sessId)
        
        # initial myself
        # the catagory of this geoserver
        self.cat = Catalog( '/'.join( (config.getConfigValue('geoserver', 'geoserveraddress'), 'rest') ),
                            config.getConfigValue('geoserver', 'admin'),
                            config.getConfigValue('geoserver', 'adminpassword') )
        
        # get the workspace that datas will be saved and if workspace not set at configure file or
        # not exit then the default workspace will be used
        self.workspace = self.cat.get_workspace ( config.getConfigValue('geoserver', 'workspace') ) 
            
        if not self.workspace:
            self.workspace = self.cat.get_default_workspace()
            
    
    def save(self, output):
        MapServer.save(self,output)
        name = "%s-%s-%s"%(output.identifier, self.process.identifier,self.sessId)
        service_url = '/'.join([config.getConfigValue('geoserver', 'geoserveraddress'), self.workspace.name])
        
        if self.datatype == "raster":         
            # save 
            logging.info("upload raster file with name: {0} ".format(name))
            self.cat.create_coveragestore(name, output.value, self.workspace, False)
            
            # construct the wcs url
            return urllib2.quote('/'.join( (service_url, 'wcs') ) +
                "?SERVICE=WCS"+ "&REQUEST=GetCoverage"+ "&VERSION=1.0.0"+
                "&COVERAGE="+name+"&CRS="+output.projection+
                "&BBOX=%s,%s,%s,%s"%(output.bbox[0],output.bbox[1],output.bbox[2],output.bbox[3])+
                "&HEIGHT=%s" %(output.height)+"&WIDTH=%s"%(output.width)+"&FORMAT=%s"%output.format["mimetype"])
        elif self.datatype == "vector":
            #save
            logging.info("upload vector file with name: {0} ".format(name))
            zip_shpf,lyname = self.compressFeatureData(output.value)
            self.cat.create_featurestore(name, zip_shpf, self.workspace, False)
            
            # construct the wfs url
            return urllib2.quote('/'.join( (service_url, 'wfs') ) +
                "?SERVICE=WFS"+ "&REQUEST=GetFeature"+ "&VERSION=1.0.0"+
                "&TYPENAME="+lyname)
        else:
            return None
    
    def compressFeatureData(self, s_ftfile):
        """
        @return:  1. the zip file path; 2. layer name at geoserver 
        """
        from osgeo import ogr
        
        def zipFiles(zipname, files, arcnames):
            assert len(files) == len(arcnames), "size of file names and rename container not equal"
            zipf = zipfile.ZipFile(zipname, 'w')
            for i in range(len(files)):
                if os.path.exists(files[i]):
                    zipf.write(files[i], arcnames[i]) 
            zipf = None
        
        ft = ogr.Open(s_ftfile)
        ftDrv = ft.GetDriver()
        
        sft = os.path.splitext(s_ftfile)[0]
        archive_files = [sft+'.shp', sft+'.shx', sft+'.prj', sft+'.dbf']
        filename = os.path.split(sft)[1]
        arcnames = [filename +'.shp', filename +'.shx', filename+'.prj', filename +'.dbf']
        
        logging.info("the driver of vector data {0} is {1}".format(s_ftfile, ftDrv.name))
        if (ftDrv.name != "ESRI Shapefile"):
            tempshpf = os.path.join(config.getConfigValue('server', 'tempPath'),str(uuid.uuid4())) 
            shpDrv = ogr.GetDriverByName("ESRI Shapefile")
            
            shpft = shpDrv.CopyDataSource(ft, tempshpf+'.shp')
            if not shpft:
                raise exceptions.IOError("{0} format vector data to shapefile format fault".format(s_ftfile))
            
            # close the vector datasource
            ft = None
            shpft = None
            
            # zip shape files and delete them
            # create an defautl prj file for this shapefile if thereis not projection information
            if not os.path.exists(tempshpf+'.prj'):
                f = open(tempshpf+'.prj', 'w')
                f.write('GEOGCS["GCS_WGS_1984",DATUM["WGS_1984",SPHEROID["WGS_1984",6378137,298.257223563]],PRIMEM["Greenwich",0],UNIT["Degree",0.017453292519943295]]')
                f.close()
            archive_files = [tempshpf+'.shp', tempshpf+'.shx', tempshpf+'.prj', tempshpf+'.dbf']
            zipFiles(tempshpf+'.zip', archive_files, arcnames)
            
            for f in archive_files:
                if os.path.exists(f):
                    os.remove(f)
            
            return tempshpf+'.zip', filename
        else:
            zipFiles(sft+'.zip', archive_files, arcnames)
            return sft+'.zip', filename
            