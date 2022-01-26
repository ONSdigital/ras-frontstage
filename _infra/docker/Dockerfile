# Dockerfile specifically for kubernetes
FROM python:3.10-slim

RUN apt update && apt install -y build-essential curl gunicorn
RUN pip install pipenv

WORKDIR /app

COPY . /app
RUN pipenv install --deploy --system

EXPOSE 8082
CMD ["gunicorn", "-b", "0.0.0.0:8080", "--workers", "4", "--timeout", "300", "frontstage:app"]

