# Dockerfile para el servidor Python - Sistema de Tickets WhatsApp con IA
FROM python:3.11-slim

WORKDIR /app

# Instalar dependencias del sistema
RUN apt-get update && apt-get install -y \
    gcc \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copiar archivos de requisitos
COPY requirements.txt .

# Instalar dependencias de Python
RUN pip install --no-cache-dir -r requirements.txt

# Copiar archivos de la aplicación
COPY main.py .
COPY index.html .

# Nota: NO copiar .env a la imagen Docker por seguridad
# Las variables de entorno se pasan via docker-compose.yml

# Crear directorios necesarios
RUN mkdir -p fotos_evidencia logs_conversaciones

# Establecer permisos
RUN chmod -R 755 fotos_evidencia logs_conversaciones

# Exponer puerto
EXPOSE 8523

# Variables de entorno por defecto (se sobrescriben con los valores en docker-compose o -e)
ENV PYTHONUNBUFFERED=1 \
    IP_LAPTOP=172.16.12.100 \
    PUERTO_LAPTOP=9000 \
    API_TOKEN=cambiar-en-produccion \
    MAX_IMAGE_SIZE=16000000 \
    CARPETA_FOTOS=fotos_evidencia \
    CARPETA_LOGS=logs_conversaciones \
    SESSION_TIMEOUT_MINUTES=15 \
    DEEPSEEK_MODEL=deepseek-chat \
    DEEPSEEK_MAX_TOKENS=2000 \
    ALLOWED_ORIGINS=* \
    DEEPSEEK_API_KEY=""

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8523/health || exit 1

# Comando para ejecutar la aplicación
CMD ["python", "main.py"]
