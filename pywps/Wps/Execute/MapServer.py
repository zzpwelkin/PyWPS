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

import logging

try:
    from osgeo import gdal
    from osgeo import ogr
except Exception,e:
    gdal=False
    logging.info("osgeo package could not be loaded, mapserver not supported: %s" %e)
    
class MapServer:
    def __init__(self, process, sessId):
        self.process = process
        self.sessId = sessId
        self.dataset = None
        self.datatype = None
    
    def save(self, output):
        """
        save the data to this map server with name
        
        @param output: :class:`pywps.Process.InAndOutputs.ComplexOutput`
        @param name: 
        
        @return: the WCS or WFS reference of this data
        """
        self.datatype = self.getDatasetType(output.value)
        output.bbox = self.getBBox(output, self.datatype)
        if self.datatype == "raster":
            output.projection = self.getProjs(self.dataset)
    
    def getDatasetType(self, data):
        """
        :param data:: data is an raster or vector file
        :returns: "raster" or "vector"
        """

        logging.debug("Importing given output [%s] using gdal" % data)
        #If dataset is XML it will make an error like ERROR 4: `/var/www/html/wpsoutputs/vectorout-26317EUFxeb' not recognised as a supported file format.
        self.dataset = gdal.Open(data)

        if self.dataset:
            return "raster"

        if not self.dataset:
            logging.debug("Importing given output [%s] using ogr" % data)
            self.dataset = ogr.Open(data)

        if self.dataset:
            return "vector"
        else:
            return None
        
    def getBBox(self,output,datatype):
        """
        :param output: :class:`pywps.Process.InAndOutputs.ComplexOutput`
        :param datatype: String raster or vector
        :return: bounding box of the dataset
        """

        if datatype == "raster":
            geotransform = self.dataset.GetGeoTransform()
            if not output.height:
                output.height = self.dataset.RasterYSize
                output.width = self.dataset.RasterXSize
            return (geotransform[0],
                    geotransform[3]+geotransform[5]*self.dataset.RasterYSize,
                    geotransform[0]+geotransform[1]*self.dataset.RasterXSize,
                    geotransform[3])
        else:
            layer = self.dataset.GetLayer()
            return layer.GetExtent()
        
    def getProjs(self, dataset):
        """
        @param dataset: raster dataset
        
        @return: return the projection with urn:ogc:def:crs:EPSG:xxxx format
        """
        assert dataset, 'dataset is None'
        from osgeo import osr
        srs = osr.SpatialReference()
        srs.ImportFromWkt(dataset.GetProjection())
        return ':'.join(['urn:ogc:def:crs', srs.GetAuthorityName("GEOGCS"), srs.GetAuthorityCode("GEOGCS")])