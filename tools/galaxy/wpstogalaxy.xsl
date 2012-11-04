<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform" xmlns:wps="http://www.opengis.net/wps/1.0.0" xmlns:ows="http://www.opengis.net/ows/1.1" xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
    <xsl:template match="/">
        <tool>
            <xsl:attribute name="id">
                <xsl:value-of select="string(//*[local-name()='ProcessDescription']/*[local-name()='Identifier'])"/>
            </xsl:attribute>
            <xsl:attribute name="name">
                <xsl:value-of select="//*[local-name()='ProcessDescription']/*[local-name()='Identifier']"/>
            </xsl:attribute>
            <xsl:attribute name="version">
                <xsl:value-of select="//*[local-name()='ProcessDescription']/@wps:processVersion"/>
            </xsl:attribute>
            <description>
                <xsl:value-of select="//*[local-name()='ProcessDescription']/*[local-name()='Title']"/>
            </description>
            <command interpreter="python">
                wps_code.py $execute_request <xsl:for-each select="//Output"> $result_<xsl:value-of select="./*[local-name()='Identifier']"/> </xsl:for-each>
            </command>
            <xsl:apply-templates select="//*[local-name()='ProcessDescription']/DataInputs"/>
            <xsl:apply-templates select="//*[local-name()='ProcessDescription']/ProcessOutputs"/>
            <xsl:apply-templates select="//*[local-name()='ProcessDescription']"/>
            <help>
                <xsl:value-of select="//*[local-name()='ProcessDescription']/*[local-name()='Abstract']"/>
            </help>
        </tool>
    </xsl:template>

    <!-- =============================================================
         DataInputs to galaxy-tool inputs 
         =========================================================== -->
    <xsl:template match="DataInputs">
        <inputs>
            <xsl:for-each select="./*[local-name()='Input']">
                <xsl:choose>
                    <xsl:when test="./@minOccurs>1">
                        <repeat>
                            <xsl:attribute name="name">
                                <xsl:value-of select="./*[local-name()='Identifier']"/>
                            </xsl:attribute>
                            <xsl:attribute name="title">
                                <xsl:value-of select="./*[local-name()='Title']"/>
                            </xsl:attribute>
                            <xsl:attribute name="min">
                                <xsl:value-of select="./@minOccurs"/>
                            </xsl:attribute>
                            <xsl:attribute name="max">
                                <xsl:value-of select="./@maxOccurs"/>
                            </xsl:attribute>
                            <xsl:apply-templates select="."/>
                        </repeat>
                    </xsl:when>
                    <xsl:otherwise>
                        <xsl:apply-templates select="."/>
                    </xsl:otherwise>
                </xsl:choose>
            </xsl:for-each>
        </inputs>
    </xsl:template>

    <!-- ============================================================
         ProcessOutputs to galaxy-tool outputs 
         =========================================================-->
    <xsl:template match="ProcessOutputs">
        <outputs>
            <xsl:for-each select="Output">
                <data format="txt">
                    <xsl:attribute name="name">
                        <xsl:value-of select="./*[local-name()='Identifier']"/>
                    </xsl:attribute>
                    <xsl:attribute name="title">
                        <xsl:value-of select="./*[local-name()='Title']"/>
                    </xsl:attribute>
                </data>
            </xsl:for-each>
        </outputs>
    </xsl:template>

    <!--  ===========================================================
                            Inputs' patam type
          ======================================================= -->
    <xsl:template match="Input">
        <param>
            <xsl:attribute name="name">
                <xsl:value-of select="./*[local-name()='Identifier']"/>
            </xsl:attribute>
            <xsl:attribute name="label">
                <xsl:value-of select="./*[local-name()='Identifier']"/>
            </xsl:attribute>
            <xsl:attribute name="help">
                <xsl:value-of select="./*[local-name()='Title']"/>
            </xsl:attribute>
            <xsl:if test="count(.//*[local-name()='DefaultValue'])=1">
                <xsl:attribute name="value">
                    <xsl:value-of select=".//*[local-name()='DefaultValue']"/>
                </xsl:attribute>
            </xsl:if>
            <xsl:if test="./@minOccurs=0">
                <xsl:attribute name="optional">true</xsl:attribute>
            </xsl:if>
            <xsl:choose>
                <!-- bbox to text data type -->
                <xsl:when test="count(./*[local-name()='BoundingBoxData'])=1">
                    <xsl:attribute name="type">text</xsl:attribute>
                </xsl:when>
                <xsl:otherwise>
                    <xsl:choose>
                        <!-- literal datat type-->
                        <xsl:when test="count(./*[local-name()='LiteralData'])=1">
                            <xsl:attribute name="type">
                                <xsl:value-of select="./*[local-name()='LiteralData']/*[local-name()='DataType']"/>
                            </xsl:attribute>
                            <xsl:if test="./*[local-name()='LiteralData']/*[local-name()='DataType']='string'">
                                <xsl:attribute name="type">text</xsl:attribute>
                            </xsl:if>
                            <xsl:if test="./*[local-name()='LiteralData']/*[local-name()='DataType']='boolean'">
                                <xsl:attribute name="label"><xsl:value-of select="./*[local-name()='Title']"/></xsl:attribute>
                                <xsl:attribute name="help"></xsl:attribute>
                                <xsl:attribute name="name">
                                    <xsl:value-of select="translate(./*[local-name()='Identifier'],'-','_')"/>
                                </xsl:attribute>
                            </xsl:if>
                        </xsl:when>
                        <xsl:otherwise>
                            <xsl:attribute name="type">data</xsl:attribute>
                            <xsl:attribute name="format">txt</xsl:attribute>
                            <xsl:attribute name="size">20</xsl:attribute>
                        </xsl:otherwise>
                    </xsl:choose>
                </xsl:otherwise>
            </xsl:choose>
        </param>
    </xsl:template>
    <!-- ================================================================
                            configures
             ============================================================-->

    <xsl:template match="ProcessDescription">
        <configfiles>
            <configfile name="execute_request">
                <wps1:Execute xmlns:wps1="http://www.opengis.net/wps/1.0.0" xmlns:ows1="http://www.opengis.net/ows/1.1" xmlns:xlink="http://www.w3.org/1999/xlink" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" service="WPS" version="1.0.0" xsi:schemaLocation="http://www.opengis.net/wps/1.0.0 ../wpsExecute_request.xsd">
                    <ows1:Identifier><xsl:value-of select="./*[local-name()='Identifier']"/></ows1:Identifier>
                    <wps1:DataInputs>
                        <xsl:for-each select="//*[local-name()='Input']">
                            <xsl:choose>
                                <!-- if mort than one input-->
                                <xsl:when test="./@minOccurs>1">
                                    #for $input in $<xsl:value-of select="./*[local-name()='Identifier']"/>
                                    #set input = $str($input['<xsl:value-of select="./*[local-name()='Identifier']"/>'])
                                    <wps1:Input>
                                        <ows1:Identifier><xsl:value-of select="./*[local-name()='Identifier']"/></ows1:Identifier>
                                        <xsl:choose>
                                            <!-- if complexdata -->
                                            <xsl:when test="count(./*[local-name()='ComplexData'])=1">
                                                #set invalue=$open($str($input)).read()
                                                <wps1:Reference xlink:href="$invalue"/>
                                            </xsl:when>
                                            <xsl:otherwise>
                                                <xsl:choose>
                                                    <!-- if literal data -->
                                                    <xsl:when test="count(./*[local-name()='LiteralData'])=1">
                                                        <wps1:Data><wps1:LiteralData>$input</wps1:LiteralData></wps1:Data>
                                                    </xsl:when>
                                                    <!-- if boundingboxdata-->
                                                    <xsl:otherwise>
                                                        <wps1:Data><wps1:LiteralData>$input</wps1:LiteralData></wps1:Data>
                                                    </xsl:otherwise>
                                                </xsl:choose>
                                            </xsl:otherwise>
                                        </xsl:choose>
                                    </wps1:Input>
                                    #end for
                                </xsl:when>
                                <xsl:otherwise>
                                    #if $<xsl:value-of select="translate(./*[local-name()='Identifier'],'-','_')"/>
                                    #set temp = "just for return"
                                    <wps1:Input>
                                        <ows1:Identifier><xsl:value-of select="./*[local-name()='Identifier']"/></ows1:Identifier>
                                        <xsl:choose>
                                            <!-- if complexdata -->
                                            <xsl:when test="count(./*[local-name()='ComplexData'])=1">
                                                #set invalue=$open($str($<xsl:value-of select="./*[local-name()='Identifier']"/>)).read()
                                                <wps1:Reference xlink:href="$invalue"/>
                                            </xsl:when>
                                            <xsl:otherwise>
                                                <xsl:choose>
                                                    <!-- if literal data -->
                                                    <xsl:when test="count(./*[local-name()='LiteralData'])=1">
                                                        <wps1:Data><wps1:LiteralData>$<xsl:value-of select="./*[local-name()='Identifier']"/></wps1:LiteralData></wps1:Data>
                                                    </xsl:when>
                                                    <!-- if boundingboxdata-->
                                                    <xsl:otherwise>
                                                        <wps1:Data><wps1:BoundingBoxData>$<xsl:value-of select="./*[local-name()='LiteralData']"/></wps1:BoundingBoxData></wps1:Data>
                                                    </xsl:otherwise>
                                                </xsl:choose>
                                            </xsl:otherwise>
                                        </xsl:choose>
                                    </wps1:Input>
                                    #end if
                                </xsl:otherwise>
                            </xsl:choose>
                        </xsl:for-each>
                    </wps1:DataInputs>
                </wps1:Execute>
            </configfile>
            <xsl:for-each select="//*[local-name()='Output']">
                <configfile>
                    <xsl:attribute name="name">result_<xsl:value-of select="./*[local-name()='Identifier']"/></xsl:attribute>
                    #echo '<xsl:value-of select="./*[local-name()='Identifier']"/>:{0}'.format($str($<xsl:value-of select="./*[local-name()='Identifier']"/>))
                </configfile>
            </xsl:for-each>
        </configfiles>
    </xsl:template>
</xsl:stylesheet>
