FROM python:3.8-slim AS build
RUN apt update && apt install -y build-essential curl
RUN pip install pipenv

WORKDIR /build
COPY Pipfile Pipfile.lock /build/
RUN bash -c 'PIPENV_VENV_IN_PROJECT=1 pipenv install --deploy --system'

FROM python:3.8-slim AS application
WORKDIR /app
COPY --from=build /build /app/
COPY . /app

EXPOSE 8082
CMD ["python", "run.py"]

HEALTHCHECK --interval=1m30s --timeout=10s --retries=3 \
  CMD curl -f http://localhost:8082/info || exit 1
