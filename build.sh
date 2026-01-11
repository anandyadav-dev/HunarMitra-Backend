#!/usr/bin/env bash
# Build script for Render deployment

set -o errexit

# Create required directories
mkdir -p logs
mkdir -p staticfiles
mkdir -p media

# Upgrade pip
pip install --upgrade pip

# Install Python dependencies
pip install -r requirements.txt

# Collect static files
python manage.py collectstatic --no-input

# Run database migrations
python manage.py migrate

# Create superuser if it doesn't exist
python create_superuser_prod.py
