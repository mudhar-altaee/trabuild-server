FROM python:3.10-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt gunicorn

# Copy backend and admin assets
COPY backend/ /app/backend/
COPY admin/ /app/admin/
COPY assets/ /app/assets/

EXPOSE 5000 10000

ENV FLASK_APP=backend/server.py
CMD ["sh", "-c", "gunicorn --bind 0.0.0.0:${PORT:-10000} --workers 2 --timeout 120 backend.server:app"]
