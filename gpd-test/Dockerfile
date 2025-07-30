FROM python:3.13-slim

WORKDIR /app

# Copy only gpd-test
COPY gpd-test/ /app/

# Install dependecies
COPY ../requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
