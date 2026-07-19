FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt \
    && apt-get update \
    && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*
COPY scraper_api.py .
COPY scraper_api.py /app/scraper_api.py

EXPOSE 3000
# Gunicorn is invoked by docker-compose command; keep a sane default here too.
CMD ["gunicorn", "-w", "2", "-b", "0.0.0.0:3000", "--timeout", "60", "scraper_api:app"]
