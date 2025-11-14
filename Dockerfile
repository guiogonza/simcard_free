FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# (opcional) herramientas mínimas
RUN apt-get update && apt-get install -y --no-install-recommends \
      curl build-essential \
    && rm -rf /var/lib/apt/lists/*

# dependencias
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# código
COPY . .

# envs por defecto (ajusta si quieres)
ENV PORT=8090 \
    FLASK_ENV=production \
    FREEEWAY_BATCH_SIZE=50 \
    FREEEWAY_ONDEMAND_WORKERS=4 \
    FREEEWAY_BG_WORKERS=6

EXPOSE 8090

# Servidor WSGI
CMD ["gunicorn", "-c", "gunicorn.conf.py", "app:app"]
