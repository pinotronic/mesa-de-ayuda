# Dockerfile para el servidor Python
FROM python:3.11-slim

WORKDIR /app

# Instalar dependencias del sistema
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copiar archivos de requisitos
COPY requirements.txt .

# Instalar dependencias de Python
RUN pip install --no-cache-dir -r requirements.txt

# Copiar archivos de la aplicación
COPY main.py .
COPY index.html .

# Crear directorio para fotos
RUN mkdir -p fotos_evidencia

# Exponer puerto
EXPOSE 8523

# Variables de entorno por defecto (se sobrescriben con .env)
ENV IP_LAPTOP=172.16.12.100 \
    PUERTO_LAPTOP=9000 \
    API_TOKEN=cambiar-en-produccion \
    MAX_IMAGE_SIZE=16000000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8523/health')" || exit 1

# Comando para ejecutar la aplicación
CMD ["python", "main.py"]
