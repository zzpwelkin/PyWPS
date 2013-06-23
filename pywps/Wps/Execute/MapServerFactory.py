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
from pywps import config

def getServer(process, sessId):
    mapserver = config.getConfigValue("server","mapserverdriver")
    
    if mapserver:
        if mapserver == "geoserver":
            from pywps.Wps.Execute import GEOS
            return GEOS.GeoServer(process, sessId)
        
        elif mapserver == "mapserver":
            from pywps.Wps.Execute import UMN
            return UMN.UMN(process, sessId)
        
        else:
            return None
        
    else:
        return None