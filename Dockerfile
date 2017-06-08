FROM python:3.5
MAINTAINER David Carboni

WORKDIR /app
COPY . /app
EXPOSE 5001
RUN pip install -r requirements.txt

ENTRYPOINT ["python3"]
CMD ["run.py"] 
