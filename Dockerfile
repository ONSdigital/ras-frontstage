FROM python:3.6-slim

WORKDIR /app
COPY . /app
EXPOSE 8082
RUN apt-get update -y && apt-get install -y python-pip
RUN pip3 install pipenv==8.3.2 && pipenv install --system --deploy

ENTRYPOINT ["python3"]
CMD ["run.py"]
