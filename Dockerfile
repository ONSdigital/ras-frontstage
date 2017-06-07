FROM python:2
MAINTAINER David Carboni

WORKDIR /app
ADD app .
RUN pip install -r requirements.txt

ENTRYPOINT python application.py
