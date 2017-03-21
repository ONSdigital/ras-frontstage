FROM python:2
MAINTAINER David Carboni

WORKDIR /ras-frontstage
ADD ras-frontstage .
RUN pip install -r requirements.txt

ENTRYPOINT python app.py
