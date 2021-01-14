# Dockerfile specifically for kubernetes
FROM python:3.9-slim

RUN apt update && apt install -y build-essential curl gunicorn
RUN pip install pipenv

WORKDIR /app

COPY . /app
RUN pipenv install --deploy --system

EXPOSE 8082
CMD ["gunicorn", "-c", "gunicorn.py", "frontstage:app"]

