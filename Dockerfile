FROM python:3.11-slim

WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose port
EXPOSE 8000

# Environment variables
ENV PORT=8000
ENV PYTHONUNBUFFERED=1
ENV MAX_CONCURRENT=5
ENV TIMEOUT=30000
ENV CACHE_TTL=900

# Start with single worker (HTTP requests are lightweight)
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
