@echo off
REM Script para detener el contenedor Docker en Windows

echo ================================
echo Deteniendo Sistema de Tickets WA
echo ================================
echo.

docker-compose down

if %ERRORLEVEL% NEQ 0 (
    echo ERROR: No se pudo detener el contenedor
    pause
    exit /b 1
)

echo.
echo ================================
echo Contenedor detenido correctamente
echo ================================
echo.
pause
