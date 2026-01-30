# Backend Dockerfile - DESARROLLO
FROM python:3.11-slim

# Establecer directorio de trabajo
WORKDIR /app

# Instalar dependencias del sistema
RUN apt-get update && apt-get install -y \
    gcc \
    curl \
    libxml2-dev \
    libxslt-dev \
    && rm -rf /var/lib/apt/lists/*

# Copiar requirements
COPY requirements.txt .

# Instalar dependencias de Python
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código de la aplicación
COPY . .

# Exponer puerto
EXPOSE 5000

# Variables de entorno para desarrollo
ENV PYTHONUNBUFFERED=1
ENV FLASK_ENV=development
ENV FLASK_DEBUG=1

# Comando para ejecutar con hot-reload
CMD ["python", "api_server.py"]