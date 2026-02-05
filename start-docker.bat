@echo off
REM Script para iniciar el contenedor Docker en Windows

echo ================================
echo Iniciando Sistema de Tickets WA
echo ================================
echo.

REM Verificar si Docker está instalado
where docker >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Docker no está instalado o no está en el PATH
    echo Descarga Docker desde: https://www.docker.com
    pause
    exit /b 1
)

REM Verificar si docker-compose está disponible
where docker-compose >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo ADVERTENCIA: docker-compose no encontrado
    echo Intentando con: docker compose
)

echo.
echo Construyendo la imagen...
docker-compose build

if %ERRORLEVEL% NEQ 0 (
    echo ERROR: No se pudo construir la imagen
    pause
    exit /b 1
)

echo.
echo Iniciando el contenedor...
docker-compose up -d

if %ERRORLEVEL% NEQ 0 (
    echo ERROR: No se pudo iniciar el contenedor
    pause
    exit /b 1
)

echo.
echo ================================
echo Contenedor iniciado correctamente
echo ================================
echo.
echo Dashboard disponible en: http://localhost:8523/
echo.
echo Comandos útiles:
echo   Ver logs:        docker-compose logs -f
echo   Detener:         docker-compose down
echo   Estado:          docker-compose ps
echo.
pause
