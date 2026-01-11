# Multi-stage Dockerfile for HunarMitra Django backend

# Stage 1: Builder
FROM python:3.11-slim as builder

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    default-libmysqlclient-dev \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

# Create and set work directory
WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --user -r requirements.txt

# Stage 2: Runtime
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DJANGO_SETTINGS_MODULE=hunarmitra.settings.dev

# Install runtime dependencies only
RUN apt-get update && apt-get install -y \
    default-libmysqlclient-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN groupadd -r django && useradd -r -g django django

# Create directories
RUN mkdir -p /app /app/staticfiles /app/media /app/logs && \
    chown -R django:django /app

# Set work directory
WORKDIR /app

# Copy Python dependencies from builder
COPY --from=builder /root/.local /home/django/.local

# Copy project files
COPY --chown=django:django . .

# Copy and set entrypoint


# Add local bin to PATH
ENV PATH=/home/django/.local/bin:$PATH

# Switch to non-root user
USER django

# Expose port
EXPOSE 8000

# Set entrypoint


# Default command
CMD ["gunicorn", "hunarmitra.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "4", "--timeout", "120"]
