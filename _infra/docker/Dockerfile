# Dockerfile specifically for kubernetes
FROM python:3.11-slim

RUN apt update && apt install -y build-essential curl gunicorn
RUN pip install pipenv

WORKDIR /app

COPY . /app
RUN pipenv install --deploy --system

CMD ["gunicorn", "-b", "0.0.0.0:9000", "--workers", "4", "--timeout", "300", "frontstage:app"]

