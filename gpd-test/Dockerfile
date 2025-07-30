FROM python:3.13-slim

WORKDIR /app

# Copy application code from gpd-test directory
COPY gpd-test/ /app/

# Copy requirements from project root (requires build from root)
COPY requirements.txt /app/

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Start the FastAPI app using uvicorn
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]

