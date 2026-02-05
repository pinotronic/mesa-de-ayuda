#!/bin/bash
# Script para detener el contenedor Docker en Linux/Mac

set -e  # Exit on error

echo "================================"
echo "Deteniendo Sistema de Tickets WA"
echo "================================"
echo ""

docker-compose down

echo ""
echo "================================"
echo "Contenedor detenido correctamente"
echo "================================"
echo ""
