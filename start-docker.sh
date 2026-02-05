#!/bin/bash
# Script para iniciar el contenedor Docker en Linux/Mac

set -e  # Exit on error

echo "================================"
echo "Iniciando Sistema de Tickets WA"
echo "================================"
echo ""

# Verificar si Docker está instalado
if ! command -v docker &> /dev/null; then
    echo "ERROR: Docker no está instalado"
    echo "Descarga Docker desde: https://www.docker.com"
    exit 1
fi

# Verificar si docker-compose está disponible
if ! command -v docker-compose &> /dev/null; then
    echo "ADVERTENCIA: docker-compose no encontrado, intentando con docker compose"
fi

echo ""
echo "Construyendo la imagen..."
docker-compose build

echo ""
echo "Iniciando el contenedor..."
docker-compose up -d

echo ""
echo "================================"
echo "Contenedor iniciado correctamente"
echo "================================"
echo ""
echo "Dashboard disponible en: http://localhost:8523/"
echo ""
echo "Comandos útiles:"
echo "  Ver logs:        docker-compose logs -f"
echo "  Detener:         docker-compose down"
echo "  Estado:          docker-compose ps"
echo ""
