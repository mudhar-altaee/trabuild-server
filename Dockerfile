FROM python:3.10-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt gunicorn

# Copy backend and admin assets
COPY backend/ /app/backend/
COPY admin/ /app/admin/
COPY assets/ /app/assets/

EXPOSE 5000

ENV FLASK_APP=backend/server.py
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "3", "backend.server:app"]
