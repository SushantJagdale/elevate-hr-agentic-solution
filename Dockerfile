# Production Dockerfile for Enterprise HR Agentic Virtual Assistant
FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python package dependencies
COPY pyproject.toml .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -e .

# Copy application source code and knowledge corpus
COPY . .

# Set environment defaults
ENV PORT=8080
ENV HOST=0.0.0.0
ENV PYTHONUNBUFFERED=1
ENV GOOGLE_CLOUD_PROJECT=learning-457908
ENV USE_VERTEXAI=TRUE

EXPOSE 8080

# Run FastAPI production server
CMD ["python", "main.py", "server", "--port", "8080", "--host", "0.0.0.0"]
