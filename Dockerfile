FROM python:3.8-slim AS build
RUN apt update && apt install -y build-essential curl
ENV PYROOT /pyroot
ENV PYTHONUSERBASE $PYROOT

COPY Pipfile Pipfile.lock ./
RUN pip install pipenv
RUN PIP_USER=1 PIP_IGNORE_INSTALLED=1 pipenv install --deploy --system

FROM python:3.8-slim AS application
ENV PYROOT /pyroot
ENV PYTHONUSERBASE $PYROOT
ENV PYTHONPATH $PYTHONPATH:/app

WORKDIR /app
COPY --from=build $PYROOT/lib/ $PYROOT/lib/
COPY . /app

EXPOSE 8082
CMD ["python", "run.py"]

HEALTHCHECK --interval=1m30s --timeout=10s --retries=3 \
  CMD curl -f http://localhost:8082/info || exit 1
