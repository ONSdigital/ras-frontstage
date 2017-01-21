FROM python
MAINTAINER David Carboni

WORKDIR /ras-frontstage
ADD ras-frontstage /ras-frontstage/
RUN pip install -r requirements.txt

CMD python start.py
