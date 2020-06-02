FROM python:3.8-slim

RUN apt update && apt install -y build-essential curl
RUN pip install poetry
RUN poetry config virtualenvs.create false

WORKDIR /app
EXPOSE 8082
CMD ["python", "run.py"]

HEALTHCHECK --interval=1m30s --timeout=10s --retries=3 \
  CMD curl -f http://localhost:8082/info || exit 1

COPY . /app
RUN poetry install
