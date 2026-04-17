FROM python:3.11-slim

WORKDIR /app

# Install dependencies first
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy ONLY backend code
COPY app ./app

# If you need these:
COPY data ./data
COPY audit_logs ./audit_logs

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]