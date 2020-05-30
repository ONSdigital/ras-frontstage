# Dockerfile specifically for kubernetes
FROM python:3.8-slim

RUN apt update && apt install -y build-essential curl gunicorn
RUN pip install poetry

WORKDIR /app

COPY . /app
RUN poetry install --no-dev

EXPOSE 8082
CMD ["gunicorn", "-c", "gunicorn.py", "frontstage:app"]

