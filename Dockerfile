# Use official Python runtime as base image
# Using Python 3.11 for better package compatibility and stability
FROM python:3.11-slim

# Set working directory in container
WORKDIR /app

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    FLASK_APP=app.py

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements file
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create instance directory for SQLite database (if used locally)
RUN mkdir -p instance

# Expose port (Cloud Run uses PORT env variable, default 8080)
EXPOSE 8080

# Run gunicorn server - use PORT env variable from Cloud Run
# Reduced workers for Cloud Run, increased timeout, preload app
CMD gunicorn --bind 0.0.0.0:${PORT:-8080} --workers 1 --threads 8 --timeout 300 --graceful-timeout 300 --preload --access-logfile - --error-logfile - --log-level info app:app
