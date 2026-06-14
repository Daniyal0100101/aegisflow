FROM python:3.11-slim

WORKDIR /app

# Install system utilities for health checks
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

# Copy dependency manifest
COPY apps/api/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy source applications and shared modules
COPY apps/api/ ./apps/api/
COPY packages/ ./packages/

# Set PYTHONPATH environment variable to resolve shared packages
ENV PYTHONPATH=/app
ENV PORT=8000

EXPOSE 8000

CMD ["python", "apps/api/main.py"]
