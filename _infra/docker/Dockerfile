# Dockerfile specifically for kubernetes
FROM python:3.8-slim

RUN apt update && apt install -y build-essential curl gunicorn

COPY requirements.txt /app/
RUN pip install -r /app/requirements.txt

WORKDIR /app

COPY . /app

EXPOSE 8082
CMD ["gunicorn", "-c", "gunicorn.py", "frontstage:app"]
