FROM python:3.12-slim

WORKDIR /app

COPY ./pyproject.toml ./

RUN apt-get update && apt-get install -y \
    postgresql-client \
    build-essential \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --upgrade pip && \
    pip install poetry && \
    poetry config virtualenvs.create false && \
    poetry install --no-root && \
    pip cache purge

COPY . .
COPY ./etl.sh /etl.sh
RUN chmod +x /etl.sh
