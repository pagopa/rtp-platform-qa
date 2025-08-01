FROM python:3.13-slim

WORKDIR /app

COPY gpd-test/ /app/

COPY requirements.txt /app/

RUN pip install --no-cache-dir -r requirements.txt

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]