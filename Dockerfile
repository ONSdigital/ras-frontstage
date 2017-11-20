FROM python:3.5
MAINTAINER David Carboni

WORKDIR /app
COPY . /app
EXPOSE 5001
RUN pip3 install pipenv==8.3.2 && pipenv install --system --deploy

ENTRYPOINT ["python3"]
CMD ["run.py"] 
