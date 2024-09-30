# Dockerfile specifically for kubernetes
FROM python:3.11-alpine

RUN apt update && apt install -y build-essential curl gunicorn
RUN pip install pipenv

WORKDIR /app
COPY . /app

RUN groupadd -r appuser && useradd -r -g appuser -u 9000 appuser && chown -R appuser:appuser .
RUN pipenv install --deploy --system

USER appuser

CMD ["gunicorn", "-b", "0.0.0.0:9000", "--workers", "4", "--timeout", "300", "frontstage:app"]

