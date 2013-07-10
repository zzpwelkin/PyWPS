import types, re

from pywps import config, DEFAULT_VERSION

def getDataTypeReference(inoutput):
    """Returns data type reference according to W3C

    :param inoutput: :class:`pywps.Process.InAndOutputs.Input`
        or :class:`pywps.Process.InAndOutputs.Output`

    :rtype: string
    :returns: url to w3.org
    """

    dataType = {"type": None, "reference": None}
    if inoutput.dataType == types.StringType:
        dataType["type"] = "string"
        dataType["reference"] = "http://www.w3.org/TR/xmlschema-2/#string"
    elif inoutput.dataType == types.FloatType:
        dataType["type"] = "float"
        dataType["reference"] = "http://www.w3.org/TR/xmlschema-2/#float"
    elif inoutput.dataType == types.IntType:
        dataType["type"] = "integer"
        dataType["reference"] = "http://www.w3.org/TR/xmlschema-2/#integer"
    elif inoutput.dataType == types.BooleanType:
        dataType["type"] = "boolean"
        dataType["reference"] = "http://www.w3.org/TR/xmlschema-2/#boolean"
    else:
        # TODO To be continued...
        dataType["type"] = "string"
        dataType["reference"] = "http://www.w3.org/TR/xmlschema-2/#string"
        pass

    return dataType

def serviceInstanceUrl(serveraddress):
    """Creates URL of GetCapabilities for this WPS

    :return: server address
    """
    if not serveraddress.endswith("?") and \
       not serveraddress.endswith("&"):
        if serveraddress.find("?") > -1:
            serveraddress += "&"
        else:
            serveraddress += "?"

    serveraddress += "service=WPS&request=GetCapabilities&version="+DEFAULT_VERSION

    serveraddress = serveraddress.replace("&", "&amp;") # Must be done first!
    serveraddress = serveraddress.replace("<", "&lt;")
    serveraddress = serveraddress.replace(">", "&gt;")

    return serveraddress

def calculateMaxInputSize(maxSize):
        """Calculates maximal size for input file based on configuration
        and units

        :return: maximum file size bytes
        """
        #maxSize = config.getConfigValue("server","maxfilesize")
        maxSize = maxSize.lower()

        units = re.compile("[gmkb].*")
        size = float(re.sub(units,'',maxSize))

        if maxSize.find("g") > -1:
            size *= 1024*1024*1024
        elif maxSize.find("m") > -1:
            size *= 1024*1024
        elif maxSize.find("k") > -1:
            size *= 1024
        else:
            size *= 1

        return size 

def formatMetadata(process):
    """Create structure suitble for template form process.metadata

    :param process: :attr:`pywps.Process`
    :returns: hash with formated metadata
    """
    
    metadata = process.metadata
    if type(metadata) == type({}):
        metadata = [metadata]

    metadatas = []
    for metad in metadata:
        metaStructure = {}

        if metad.has_key("title"):
            metaStructure["title"] = metad["title"]
        else:
            metaStructure["title"] = process.title

        if metad.has_key("href"):
            metaStructure["href"] = metad["href"]
        else:
            metaStructure["href"] = config.getConfigValue("wps","serveraddress")+\
                    "?service=WPS&amp;request=DescribeProcess&amp;version="+config.getConfigValue("wps","version")+\
                    "&amp;identifier="+ process.identifier

        metadatas.append(metaStructure)
        
    return metadatas

def statusLocationFiletoUrl(filePath):
    return filePath.replace(config.getConfigValue('server', 'outputPath'), config.getConfigValue('server', 'outputUrl'))

def statusLocationUrltoFile(urlPath):
    return urlPath.replace(config.getConfigValue('server', 'outputUrl'), config.getConfigValue('server', 'outputPath'))