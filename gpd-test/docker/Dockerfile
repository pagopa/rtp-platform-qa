FROM python:3.13-slim@sha256:4c2cf9917bd1cbacc5e9b07320025bdb7cdf2df7b0ceaccb55e9dd7e30987419

WORKDIR /app

COPY pyproject.toml /app/

RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir hatchling

COPY . /app/

RUN pip install --no-cache-dir -e ".[dev]" \
    && pip install --no-cache-dir aiokafka==0.12.0

WORKDIR /app/gpd-test

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
