#!/bin/bash
if ! [ -a .build ] ; then
	echo "Creating Virtual Environment"
	virtualenv .build -p python3
fi
source .build/bin/activate
pip3 install -r requirements.txt --upgrade
API_GATEWAY_AGGREGATED_SURVEYS_URL=http://surveysvc-int.apps.devtest.onsclofo.uk \
SM_URL=http://ras-secure-messaging-int.apps.devtest.onsclofo.uk \
ONS_OAUTH_SERVER=ras-django-int.apps.devtest.onsclofo.uk \
RM_CASE_SERVICE_PORT=80 RM_CASE_SERVICE_HOST=casesvc-int.apps.devtest.onsclofo.uk \
python3 run.py
