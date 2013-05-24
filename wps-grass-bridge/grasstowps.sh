#!/bin/bash

pywps_service="./pywps_services"

test -d /tmp/grasstowps || mkdir /tmp/grasstowps

for prs in $@;do
	outprs=`echo $prs|awk -F. 'ORS="_" {for(i=1;i<=NF;i++) print $i}'`
	test -f $pywps_service/$outprs.py&&echo "Waring:$outprs.py have exited"&&continue 
	$prs --wps-process-description > /tmp/grasstowps/$prs.xml
	echo $outprs
	python GrassXMLtoPyWPS.py -x /tmp/grasstowps/$prs.xml -p $pywps_service/$outprs.py
	echo "'$outprs'," >> $pywps_service/__init__.py
done

#format the __init__.py file
awk -F] 'ORS=" " {for(i=1;i<=NF;i++) print $i}' $pywps_service/__init__.py > /tmp/grasstowps/__init__.py
echo "]" >> /tmp/grasstowps/__init__.py
cat /tmp/grasstowps/__init__.py > $pywps_service/__init__.py

test -d /tmp/grasstowps && rm -rf /tmp/grasstowps
