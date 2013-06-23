import types

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