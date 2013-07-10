import types

############## COMPLEX DATA FORMAT ############### 
RASTER_MIMETYPES_LIST = [('IMAGE/TIFF', "IMAGE/TIFF"), ('IMAGE/GEOTIFF',"IMAGE/GEOTIFF")]
VECTOR_MIMETYPES_LIST = [('GML','TEXT/XML'), ('GML','APPLICATION/XML'), ('','APPLICATION/SHP'), ('',"APPLICATION/X-ZIPPED-SHP")]
VECTOR_SCHEMA_LIST = [('','GML'), ('','KML')]

# All supported import raster formats
RASTER_MIMETYPES = [{"MIMETYPE":"IMAGE/TIFF", "GDALID":"GTiff"},
                           {"MIMETYPE":"IMAGE/PNG", "GDALID":"PNG"}, \
                           {"MIMETYPE":"IMAGE/GIF", "GDALID":"GIF"}, \
                           {"MIMETYPE":"IMAGE/JPEG", "GDALID":"JPEG"}, \
                           {"MIMETYPE":"IMAGE/GEOTIFF", "GDALID":"GTiff"}, \
                           {"MIMETYPE":"APPLICATION/X-ERDAS-HFA", "GDALID":"HFA"}, \
                           {"MIMETYPE":"APPLICATION/NETCDF", "GDALID":"netCDF"}, \
                           {"MIMETYPE":"APPLICATION/X-NETCDF", "GDALID":"netCDF"}, \
                           {"MIMETYPE":"APPLICATION/GEOTIFF", "GDALID":"GTiff"}, \
                           {"MIMETYPE":"APPLICATION/X-GEOTIFF", "GDALID":"GTiff"}]

# All supported input vector formats [mime type, schema]
VECTOR_MIMETYPES = [{"MIMETYPE":"TEXT/XML", "SCHEMA":"GML", "GDALID":"GML"}, \
                           {"MIMETYPE":"TEXT/XML", "SCHEMA":"KML", "GDALID":"KML"}, \
                           {"MIMETYPE":"APPLICATION/XML", "SCHEMA":"GML", "GDALID":"GML"}, \
                           {"MIMETYPE":"APPLICATION/XML", "SCHEMA":"KML", "GDALID":"KML"}, \
                           {"MIMETYPE":"APPLICATION/DGN", "SCHEMA":"", "GDALID":"DGN"}, \
                           {"MIMETYPE":"APPLICATION/X-ZIPPED-SHP", "SCHEMA":"", "GDALID":"ESRI_Shapefile"}, \
                           {"MIMETYPE":"APPLICATION/SHP", "SCHEMA":"", "GDALID":"ESRI_Shapefile"}]

# All supported space time dataset formats
STDS_MIMETYPES = [ {"MIMETYPE":"APPLICATION/X-GRASS-STRDS-TAR", "STDSID":"STRDS", "COMPRESSION":"NO"}, \
                           {"MIMETYPE":"APPLICATION/X-GRASS-STRDS-TAR-GZ", "STDSID":"STRDS", "COMPRESSION":"GZIP"}, \
                           {"MIMETYPE":"APPLICATION/X-GRASS-STRDS-TAR-BZIP", "STDSID":"STRDS", "COMPRESSION":"BZIP2"}, \
                           {"MIMETYPE":"APPLICATION/X-GRASS-STVDS-TAR", "STDSID":"STVDS", "COMPRESSION":"NO"}, \
                           {"MIMETYPE":"APPLICATION/X-GRASS-STVDS-TAR-GZ", "STDSID":"STVDS", "COMPRESSION":"GZIP"}, \
                           {"MIMETYPE":"APPLICATION/X-GRASS-STVDS-TAR-BZIP", "STDSID":"STVDS", "COMPRESSION":"BZIP2"}]

#################### LITERAL DATA TYPE #################
LITERALDATATYPE = [('boolean','boolean'), ('integer','integer'), ('float','float'), ('string','string'), ]

#################### UOM LIST ####################
UOM = [('*','*'), ('meter','meter'), ]

#################### PROCESS TYPE LIST #############
PROCESS_TYPE_LIST = (('pywps.jobs.jobs.NormalProcessJob', 'Normal Process'), )

#################### simple type map #################
TYPE_MAP = {'integer':types.IntType, 'string':types.StringType, 'float':types.FloatType,
            'boolean':types.BooleanType}