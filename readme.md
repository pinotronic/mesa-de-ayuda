# 🎫 Sistema de Tickets WhatsApp con IA

Sistema profesional de gestión de tickets de soporte técnico a través de WhatsApp, con clasificación automática mediante IA, almacenamiento de evidencias fotográficas y panel web de administración.

## 🏗️ Arquitectura

- **Laptop (Desktop):** Puente de WhatsApp con Node.js + Baileys
- **Servidor (Docker):** Backend FastAPI + SQLite + Panel Web
- **Comunicación:** REST API con autenticación Bearer Token
- **Persistencia:** Base de datos SQLite + Almacenamiento de imágenes

## ✨ Características

### 🔐 Seguridad
- ✅ Autenticación con Bearer Token
- ✅ Validación de tamaño de imágenes (máx 16MB)
- ✅ CORS configurable
- ✅ Logs estructurados
- ✅ Health checks automáticos

### 🔄 Confiabilidad
- ✅ Sistema de reintentos con backoff exponencial
- ✅ Cola local de mensajes (persistencia ante fallos)
- ✅ Reconexión automática de WhatsApp
- ✅ Manejo robusto de errores

### 📊 Funcionalidades
- ✅ Recepción automática de tickets por WhatsApp
- ✅ Clasificación inteligente por IA (Hardware/Software)
- ✅ Almacenamiento de evidencias fotográficas
- ✅ Panel web responsive con Tailwind CSS
- ✅ **💬 Chat en vivo técnico-usuario** (NUEVO)
- ✅ Notificaciones automáticas a clientes
- ✅ Actualización en tiempo real
- ✅ Historial completo de conversaciones
- ✅ Conversación interactiva con flujo guiado por IA

## 🚀 Inicio Rápido

Ver [DEPLOY.md](DEPLOY.md) para guía completa de instalación.

### Laptop (WhatsApp Bridge)

```bash
npm install
cp .env.laptop.example .env
# Editar .env con configuración
npm start
# Escanear QR de WhatsApp
```

### Servidor (Docker)

```bash
cp .env.example .env
# Editar .env con configuración
docker-compose up -d
```

## 📚 Documentación

- [DEPLOY.md](DEPLOY.md) - Guía completa de despliegue paso a paso
- [CHAT-EN-VIVO.md](CHAT-EN-VIVO.md) - Sistema de chat interactivo técnico-usuario
- [FIX-NUMEROS-LID.md](FIX-NUMEROS-LID.md) - Solución para formato LID de WhatsApp
- [.env.example](.env.example) - Configuración del servidor
- [.env.laptop.example](.env.laptop.example) - Configuración de laptop

---

## 💻 Ejecutar como Servicio en Windows (PM2)

### Paso 1: Instalar PM2

```bash
npm install -g pm2
npm install -g pm2-windows-startup
```

### Paso 2: Registrar como servicio

```bash
# Iniciar el proceso
pm2 start whatsapp-bridge.js --name "bot-reparaciones"

# Configurar inicio automático
pm2-startup install
pm2 save
```

# Ver que el servidor responde
curl http://172.16.12.199:8523/tickets

# 1. Detener el puente (Ctrl+C en la terminal donde corre)

# 2. Eliminar la carpeta de sesión
Remove-Item -Recurse -Force sesion_wa

# 3. Reiniciar
npm start