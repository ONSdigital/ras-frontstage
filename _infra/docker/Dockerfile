# Dockerfile specifically for kubernetes
FROM python:3.8-slim

RUN apt update && apt install -y build-essential curl gunicorn
RUN pip install pipenv

WORKDIR /app

COPY . /app
RUN pipenv install --deploy --system

EXPOSE 8082
CMD ["gunicorn", "app:app", "--timeout 120", "-c", "gunicorn.py", "frontstage:app"]

