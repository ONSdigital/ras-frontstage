# Dockerfile specifically for kubernetes
FROM python:3.8-slim AS build
RUN apt update && apt install -y build-essential curl gunicorn
RUN pip install pipenv

WORKDIR /build
COPY Pipfile Pipfile.lock /build/
RUN bash -c 'PIPENV_VENV_IN_PROJECT=1 pipenv install --deploy --system'

FROM python:3.8-slim AS application
WORKDIR /app
COPY --from=build /build /app/
COPY . /app

EXPOSE 8082
CMD ["gunicorn", "-c", "gunicorn.py", "frontstage:app"]

