# 🐳 Guía de Despliegue con Docker

## Prerequisitos
- Docker instalado (https://www.docker.com)
- Docker Compose instalado (generalmente viene con Docker Desktop)
- Tu API Key de DeepSeek (https://platform.deepseek.com)

---

## 🚀 Opción 1: Usando Docker Compose (Recomendado)

### Paso 1: Configurar variables de entorno
Crea un archivo `.env.docker` en la raíz del proyecto:

```bash
DEEPSEEK_API_KEY=sk-xxxxxxxxxxxxxx
```

O modifica el `docker-compose.yml` directamente con tu API Key.

### Paso 2: Construir y ejecutar

```bash
# Construir la imagen (solo la primera vez)
docker-compose build

# Ejecutar el contenedor
docker-compose up -d

# Ver logs en tiempo real
docker-compose logs -f whatsapp-tickets-api

# Detener el contenedor
docker-compose down
```

### Paso 3: Verificar que está funcionando

```bash
# Ver estado del contenedor
docker-compose ps

# Hacer health check manual
curl http://localhost:8523/health

# Acceder al dashboard
# http://localhost:8523/
```

---

## 🐳 Opción 2: Usando solo Docker (sin Compose)

### Paso 1: Construir la imagen

```bash
docker build -t whatsapp-tickets:latest .
```

### Paso 2: Ejecutar el contenedor

```bash
docker run -d \
  --name whatsapp-tickets-server \
  -p 8523:8523 \
  -e DEEPSEEK_API_KEY=sk-xxxxxxxxxxxxxx \
  -e IP_LAPTOP=172.16.12.100 \
  -e PUERTO_LAPTOP=9000 \
  -e API_TOKEN=1234567890 \
  -v $(pwd)/fotos_evidencia:/app/fotos_evidencia \
  -v $(pwd)/logs_conversaciones:/app/logs_conversaciones \
  -v $(pwd)/tickets.db:/app/tickets.db \
  whatsapp-tickets:latest
```

### Paso 3: Ver logs

```bash
docker logs -f whatsapp-tickets-server
```

---

## 📊 Verificaciones Importantes

### 1. Verificar que el contenedor está corriendo
```bash
docker ps | grep whatsapp-tickets
```

### 2. Verificar logs
```bash
docker-compose logs whatsapp-tickets-api
```

### 3. Hacer request al servidor
```bash
# Health check
curl -X GET http://localhost:8523/health

# Listar tickets
curl -X GET http://localhost:8523/tickets
```

### 4. Verificar que los volúmenes están montados
```bash
# Ver contenido del contenedor
docker exec whatsapp-tickets-server ls -la /app/

# Ver si existen las carpetas
docker exec whatsapp-tickets-server ls -la /app/fotos_evidencia
docker exec whatsapp-tickets-server ls -la /app/logs_conversaciones
```

---

## ⚙️ Variables de Entorno Disponibles

| Variable | Valor Por Defecto | Descripción |
|----------|------------------|-------------|
| `DEEPSEEK_API_KEY` | (vacío) | **REQUERIDO** - Tu API Key de DeepSeek |
| `IP_LAPTOP` | 172.16.12.100 | IP de la máquina con el puente WhatsApp |
| `PUERTO_LAPTOP` | 9000 | Puerto del puente WhatsApp |
| `API_TOKEN` | cambiar-en-produccion | Token para autenticación |
| `SESSION_TIMEOUT_MINUTES` | 15 | Timeout de sesiones conversacionales |
| `DEEPSEEK_MODEL` | deepseek-chat | Modelo de DeepSeek a usar |
| `DEEPSEEK_MAX_TOKENS` | 2000 | Máximo de tokens en respuestas IA |
| `ALLOWED_ORIGINS` | * | Orígenes CORS permitidos |

---

## 📁 Volúmenes y Persistencia

El `docker-compose.yml` monta estos volúmenes:

- `./fotos_evidencia` → Evidencias fotográficas de tickets
- `./logs_conversaciones` → Logs de conversaciones
- `./tickets.db` → Base de datos SQLite

Estos directorios se crean automáticamente si no existen.

---

## 🔧 Troubleshooting

### Error: "Port 8523 already in use"
```bash
# Cambiar el puerto en docker-compose.yml o usar otro puerto
docker-compose down  # Detener otros contenedores
```

### Error: "DEEPSEEK_API_KEY is empty"
```bash
# Asegúrate de agregar tu API Key en docker-compose.yml
# Línea: DEEPSEEK_API_KEY: "${DEEPSEEK_API_KEY}"
# O:     DEEPSEEK_API_KEY: "sk-xxxxxxxxxxxxxx"
```

### Error: "Connection refused" desde whatsapp-bridge.js
Verifica que:
1. El IP_LAPTOP es correcto (donde está el puente)
2. El PUERTO_LAPTOP es correcto (9000 por defecto)
3. El API_TOKEN coincide en ambos archivos

### Ver logs detallados
```bash
docker-compose logs -f --tail=100 whatsapp-tickets-api
```

---

## 📊 Monitoreo Continuo

```bash
# Ver estado y recursos
docker stats whatsapp-tickets-server

# Ver eventos del contenedor
docker events --filter "container=whatsapp-tickets-server"
```

---

## 🔐 Producción - Recomendaciones

1. **API Key**: Usa variables de entorno, nunca hardcodees
2. **Restart Policy**: Ya está configurado como `unless-stopped`
3. **Health Checks**: Ya están configurados
4. **Logs**: Usa `docker logs` o mejor aún, un servicio de logging
5. **Network**: Considera usar una red privada en Docker

---

## 📋 Checklist de Despliegue

- [ ] Docker instalado y funcionando
- [ ] API Key de DeepSeek configurada
- [ ] Archivo docker-compose.yml editado con tus valores
- [ ] IP_LAPTOP y PUERTO_LAPTOP correctos
- [ ] API_TOKEN igual en whatsapp-bridge.js
- [ ] Puerto 8523 disponible
- [ ] `docker-compose up -d` ejecutado exitosamente
- [ ] `curl http://localhost:8523/health` responde con status "ok"
- [ ] Dashboard accesible en http://localhost:8523/
- [ ] Puente WhatsApp conectando correctamente

---

## 📞 Soporte

Si hay problemas:
1. Revisa los logs: `docker-compose logs -f`
2. Verifica variables de entorno: `docker exec whatsapp-tickets-server env`
3. Testa conectividad: `docker exec whatsapp-tickets-server curl http://localhost:8523/health`

