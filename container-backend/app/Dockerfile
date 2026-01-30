FROM python:3.14-slim AS builder

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose the port
EXPOSE 8000

# Run the Flask app with gunicorn for production
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "app:app"]
