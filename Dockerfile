# Gunakan base image Python slim
FROM python:3.12-slim

# Install OS-level dependencies
RUN apt-get update && apt-get install -y \
    build-essential libpq-dev curl && \
    rm -rf /var/lib/apt/lists/*

# Buat direktori kerja
WORKDIR /app

# Salin file requirement dan install pip dependencies
COPY requirements.txt .

RUN pip install --upgrade pip && pip install -r requirements.txt

# Salin semua file proyek ke container
COPY . .

# Jalankan collectstatic tanpa interaktif
RUN python manage.py collectstatic --noinput

# Set environment variable default (dapat di-overwrite di runtime)
ENV DJANGO_SETTINGS_MODULE=Sizopi.settings
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Expose port (sesuai gunicorn)
EXPOSE 8000

# Gunakan gunicorn sebagai WSGI server
CMD ["gunicorn", "Sizopi.wsgi:application", "--bind", "0.0.0.0:8000"]