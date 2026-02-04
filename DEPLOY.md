# 🚀 Guía de Despliegue - Sistema de Tickets WhatsApp

## 📋 Arquitectura del Sistema

```
┌─────────────────┐         HTTP/HTTPS          ┌──────────────────┐
│  LAPTOP         │◄──────────────────────────►│  SERVIDOR        │
│  (Escritorio)   │                             │  (Docker)        │
├─────────────────┤                             ├──────────────────┤
│ whatsapp-bridge │  POST /webhook              │ main.py          │
│     (Node.js)   ├────────────────────────────►│   (FastAPI)      │
│                 │                             │                  │
│  ┌──────────┐   │  POST /enviar-mensaje       │  ┌────────────┐  │
│  │ WhatsApp │   │◄────────────────────────────┤  │ SQLite DB  │  │
│  │ (Baileys)│   │                             │  └────────────┘  │
│  └──────────┘   │                             │  ┌────────────┐  │
│  ┌──────────┐   │                             │  │ index.html │  │
│  │  Cola    │   │                             │  └────────────┘  │
│  │ Local    │   │                             │                  │
│  └──────────┘   │                             │                  │
└─────────────────┘                             └──────────────────┘
     :9000                                            :8523
```

---

## 🖥️ PARTE 1: Configuración del Servidor (Docker)

### 1. Preparar el Servidor

```bash
# Crear directorio del proyecto
mkdir -p /opt/whatsapp-tickets
cd /opt/whatsapp-tickets

# Copiar archivos necesarios
# - Dockerfile
# - docker-compose.yml
# - main.py
# - index.html
# - requirements.txt
```

### 2. Configurar Variables de Entorno

```bash
# Copiar archivo de ejemplo
cp .env.example .env

# Editar con las IPs reales
nano .env
```

**Contenido de `.env`:**
```env
# IMPORTANTE: Obtener la IP real de la laptop ejecutando ipconfig en Windows
# Buscar la dirección IPv4 de la interfaz de red principal
IP_LAPTOP=172.16.76.153        # IP REAL de la laptop (ejemplo)
PUERTO_LAPTOP=9000
API_TOKEN=mi-token-secreto-super-seguro-2026
MAX_IMAGE_SIZE=16000000
ALLOWED_ORIGINS=*
```

**⚠️ CRÍTICO:** La IP_LAPTOP debe ser la IP **real** de la laptop en tu red, no un valor de ejemplo.

### 3. Construir y Ejecutar con Docker

```bash
# Construir la imagen (IMPORTANTE: usar --no-cache para evitar problemas)
docker compose build --no-cache

# Iniciar el servicio
docker compose up -d

# Ver logs para verificar que inició correctamente
docker compose logs -f

# Verificar estado
docker compose ps
```

**⚠️ IMPORTANTE:** Si actualizas el código de `main.py`, siempre usa `--no-cache`:
```bash
docker compose build --no-cache
docker compose down
docker compose up -d
```

### 4. Verificar Funcionamiento

```bash
# Health check
curl http://localhost:8523/health

# Debería responder:
# {"status":"ok","total_tickets":0,"laptop_url":"http://172.16.12.100:9000","timestamp":"..."}
```

### 5. Firewall (si es necesario)

```bash
# Ubuntu/Debian
sudo ufw allow 8523/tcp

# CentOS/RHEL
sudo firewall-cmd --permanent --add-port=8523/tcp
sudo firewall-cmd --reload
```

---

## 💻 PARTE 2: Configuración de la Laptop (WhatsApp Bridge)

### 1. Requisitos Previos

- **Node.js** versión 16 o superior
- Conexión a Internet
- Mismo segmento de red que el servidor

### 2. Instalación

```bash
# En la laptop, crear directorio
mkdir whatsapp-bridge
cd whatsapp-bridge

# Copiar archivos:
# - whatsapp-bridge.js
# - package.json
# - .env.laptop.example
```

### 3. Configurar Variables de Entorno

```powershell
# Copiar archivo de ejemplo
Copy-Item .env.laptop.example .env

# Editar con datos del servidor
notepad .env
```

**Contenido de `.env`:**
```env
# IP del servidor Docker - obtenerla ejecutando en el servidor:
# ip addr show | grep "inet 172"
SERVER_URL=http://172.16.12.199:8523    # IP REAL del servidor
PUERTO_LOCAL=9000
API_TOKEN=mi-token-secreto-super-seguro-2026   # MISMO que el servidor
```

**⚠️ CRÍTICO:** 
- `SERVER_URL` debe tener la IP **real** del servidor
- `API_TOKEN` debe ser **exactamente igual** al del servidor

### 4. Instalar Dependencias

```bash
# Instalar paquetes de Node.js
npm install
```

### 5. Iniciar el Puente de WhatsApp

```bash
# Ejecutar
npm start

# O con nodemon para desarrollo
npm run dev
```

### 6. Escanear QR de WhatsApp

```
┌───────────────────────────────────────────┐
│ IMPORTANTE: Escaneo de QR                 │
├───────────────────────────────────────────┤
│ 1. Se mostrará un código QR en terminal  │
│ 2. Abrir WhatsApp en tu teléfono         │
│ 3. Ir a Dispositivos Vinculados          │
│ 4. Escanear el QR de la terminal         │
│ 5. Esperar mensaje: ✅ Conectado         │
└───────────────────────────────────────────┘
```

**⚠️ Si no aparece el QR:**
```powershell
# Detener (Ctrl+ PowerShell:

```powershell
# Health check del puente
curl http://localhost:9000/health

# Debería responder:
# {"status":"ok","whatsapp":"conectado","cola_pendiente":0,"uptime":123.45}
```

**⚠️ Si muestra "whatsapp":"desconectado":**
```powershell
# Ver logs en la terminal donde corre npm start
# Debería decir: ✅ Conectado a WhatsApp y listo
# Si no, reiniciar y escanear QR de nuevo
- Verifica que la sesión no haya expirado en tu teléfono
- Elimina `sesion_wa` y escanea de nuevo
- Asegúrate de tener conexión a Internet estable

### 7. Verificar Conexión

En otra terminal:

```bash
# Health check del puente
curl http://localhost:9000/health

# Debería responder:
# {"status":"ok","whatsapp":"conectado","cola_pendiente":0,"uptime":123.45}
```

---

## 🔐 Configuración de Seguridad

### 1. Generar Token Seguro

```bash
# Generar token aleatorio
openssl rand -hex 32

# Usar este valor en API_TOKEN de ambos archivos .env
```

### 2. Restringir CORS (Servidor)

En el servidor, editar `.env`:
```env
# En lugar de *, especificar orígenes permitidos
ALLOWED_ORIGINS=http://172.16.12.199:8523,https://tu-dominio.com
```

### 3. Firewall de la Laptop

```bash
# Windows (PowerShell como Admin)
New-NetFirewallRule -DisplayName "WhatsApp Bridge" -Direction Inbound -LocalPort 9000 -Protocol TCP -Action Allow

# Linux
sudo ufw allow from 172.16.12.199 to any port 9000
```

---

## 📊 Monitoreo y Mantenimiento

### Logs del Servidor

```bash
# Ver logs en tiempo real
docker-compose logs -f

# Ver solo errores
docker-compose logs | grep ERROR

# Ver últimas 100 líneas
docker-compose logs --tail=100
```

### Logs de la Laptop

Los logs se muestran directamente en la terminal donde ejecutaste `npm start`.

### Health Checks Automáticos

```bash
# Crear script de monitoreo (servidor)
cat > /opt/health_check.sh << 'EOF'
#!/bin/bash
if ! curl -f http://localhost:8523/health > /dev/null 2>&1; then
    echo "⚠️ Servidor caído, reiniciando..."
    cd /opt/whatsapp-tickets && docker-compose restart
fi
EOF

chmod +x /opt/health_check.sh

# Agregar a cron (cada 5 minutos)
crontab -e
# Agregar línea:
*/5 * * * * /opt/health_check.sh
```

### Backup Automático

```bash
# Script de backup (servidor)
cat > /opt/backup.sh << 'EOF'
#!/bin/bash
FECHA=$(date +%Y%m%d_%H%M%S)
tar -czf /backup/tickets_${FECHA}.tar.gz \
    /opt/whatsapp-tickets/tickets.db \
    /opt/whatsapp-tickets/fotos_evidencia
# Mantener solo últimos 7 días
find /backup -name "tickets_*.tar.gz" -mtime +7 -delete
EOF

chmod +x /opt/backup.sh

# Ejecutar diariamente a las 2 AM
crontab -e
# Agregar:
0 2 * * * /opt/backup.sh
```
, error 422 o timeouts

**Soluciones:**
```bash
# 1. Verificar conectividad
ping 172.16.12.199

# 2. Verificar puerto abierto
telnet 172.16.12.199 8523
# o
nc -zv 172.16.12.199 8523

# 3. Revisar token en ambos .env (deben ser IDÉNTICOS)
# Laptop: cat .env | grep API_TOKEN
# Servidor: cat .env | grep API_TOKEN

# 4. Verificar IP de laptop configurada en servidor
# Desde laptop ejecutar: ipconfig
# Verificar que IP_LAPTOP en servidor .env coincida

# 5. Si sigue error 422, reconstruir imagen Docker
docker compose build --no-cache
docker compose down
docker compose up -d
# 2. Verificar puerto abierto
telnet 172.16.12.199 8523muestra "undefined" o error

**Soluciones:**
```powershell
# 1. Verificar que WhatsApp esté conectado
curl http://localhost:9000/health
# Debe decir: "whatsapp":"conectado"

# 2. Si está desconectado, reiniciar puente
# Ctrl+C
npm start

# 3. Desde el servidor, verificar laptop
curl http://172.16.76.153:9000/health

# 4. Verificar IP correcta en servidor .env
# Desde laptop: ipconfig (obtener IP real)
# En servidor: cat .env | grep IP_LAPTOP
# Deben coincidir

# 5. Si falla, verificar:
# - Laptop encendida
# - whatsapp-bridge.js ejecutándose
# -ntomas:** Botón "Notificar Recibido" falla

**Soluciones:**
```bash
# Desde el servidor, verificar laptop
curl http://172.16.12.100:9000/health

# Si falla, verificar:
# 1. Laptop encendida
# 2. whatsapp-bridge.js ejecutándose
# 3. Firewall de laptop permite conexiones desde servidor
```
, health check muestra "desconectado"

**Soluciones:**
```powershell
# Opción 1: Reiniciar el puente
# Ctrl+C en la terminal
npm start

# Opción 2: Limpiar sesión y reconectar
# Detener con Ctrl+C
Remove-Item -Recurse -Force sesion_wa
npm start
# Escanear nuevo QR

# Opción 3: Verificar en el teléfono
# WhatsApp > Dispositivos Vinculados
# Verificar que el dispositivo aparezca activo
# Si no, eliminar y vincular de nuevo
```
# Aumentar límite en servidor .env
MAX_IMAGE_SIZE=32000000  # 32MB
```

### Problema: WhatsApp desconectado

**Síntomas:** QR desaparece, mensajes no entran

**Soluciones:**
1. Detener `whatsapp-bridge.js` (Ctrl+C)
2. Eliminar carpeta `sesion_wa`
3. Reiniciar `npm start`
4. Escanear nuevo QR

---

## 🔄 Actualización del Sistema

### Actualizar Servidor

```bash
cd /opt/whatsapp-tickets

# Detener contenedor
docker-compose down

# Actualizar archivos (main.py, etc.)
# ...

# Reconstruir y reiniciar
docker-compose build
docker-compose up -d
```

### Actualizar Laptop

```bash
**⚠️ Importante:** Para ver el panel HTML, acceder a:
- ✅ Correcto: `http://172.16.12.199:8523/`
- ❌ Incorrecto: `http://172.16.12.199:8523/tickets` (esto muestra JSON)

### Notificar Recepción

1. Abrir panel web
2. Click en "Notificar Recibido" del ticket
3. Cliente recibe mensaje automático de confirmación

**⚠️ Si el botón falla:**
- Verificar que WhatsApp esté conectado: `curl http://localhost:9000/health`
- Verificar que muestre `"whatsapp":"conectado"`
- Si muestra "desconectado", reconectar el puente
# ...

# Reinstalar dependencias si package.json cambió
npm install

# Reiniciar
npm start
```

---

## 📱 Uso del Sistema

### Enviar Ticket desde WhatsApp

1. Cliente envía mensaje al número vinculado
2. Opcionalmente adjunta foto del equipo
3. Sistema crea ticket automáticamente
4. Aparece en panel web: `http://IP-SERVIDOR:8523`

### Notificar Recepción

1. Abrir panel web
2. Click en "Notificar Recibido" del ticket
3. Cliente recibe mensaje automático de confirmación

---

## 🛡️ Mejores Prácticas

1. **Token Seguro:** Usar tokens de al menos 32 caracteres
2. **Backups:** Configurar backups automáticos diarios
3. **Monitoreo:** Configurar alertas de health check
4. **Logs:** Revisar logs semanalmente
5. **Actualizaciones:** Mantener dependencias actualizadas
6. **HTTPS:** Considerar usar reverse proxy con SSL/TLS
7. **VPN:** Si es posible, conectar laptop y servidor por VPN

---

## 📞 Comandos Rápidos

### Servidor
- [ ] Docker instalado
- [ ] Archivos copiados (main.py, index.html, Dockerfile, docker-compose.yml, requirements.txt)
- [ ] `.env` creado y configurado con IP real de laptop
- [ ] Puerto 8523 abierto en firewall
- [ ] `docker compose build --no-cache` ejecutado
- [ ] `docker compose up -d` ejecutado
- [ ] Health check OK: `curl http://localhost:8523/health`
- [ ] Panel web accesible: `http://IP-SERVIDOR:8523/`

### Laptop
- [ ] Node.js instalado
- [ ] Archivos copiados (whatsapp-bridge.js, package.json)
- [ ] `.env` creado y configurado con IP real del servidor
- [ ] `npm install` ejecutado
- [ ] `npm start` ejecutado
- [ ] QR escaneado con WhatsApp
- [ ] WhatsApp CONECTADO (verificar en logs)
- [ ] Health check OK: `curl http://localhost:9000/health`
- [ ] Health check muestra `"whatsapp":"conectado"`

### Configuración
- [ ] Tokens idénticos en ambos .env (servidor y laptop)
- [ ] IP_LAPTOP en servidor coincide con IP real de laptop (ipconfig)
- [ ] SERVER_URL en laptop coincide con IP real del servidor

### Pruebas
- [ ] Enviar mensaje de WhatsApp al número vinculado
- [ ] Ticket aparece en panel web (http://IP-SERVIDOR:8523/)
- [ ] Click en "Notificar Recibido" funciona
- [ ] Cliente recibe mensaje de confirmación por WhatsApp

## ✅ Checklist de Despliegue

- [ ] Servidor: Docker instalado
- [ ] Servidor: Archivos copiados
- [ ] Servidor: `.env` configurado
- [ ] Servidor: Puerto 8523 abierto
- [ ] Servidor: `docker-compose up -d` ejecutado
- [ ] Servidor: Health check OK
- [ ] Laptop: Node.js instalado
- [ ] Laptop: Archivos copiados
- [ ] Laptop: `.env` configurado
- [ ] Laptop: `npm install` ejecutado
- [ ] Laptop: `npm start` ejecutado
- [ ] Laptop: QR escaneado
- [ ] Laptop: WhatsApp conectado
- [ ] Laptop: Health check OK
- [ ] Tokens idénticos en ambos .env
- [ ] Prueba: Enviar mensaje de WhatsApp
- [ ] Prueba: Ticket aparece en panel
- [ ] Prueba: "Notificar Recibido" funciona
