# 🚀 Guía Rápida de Despliegue

## Antes de Empezar
1. Tener Docker instalado: https://www.docker.com
2. Tener tu API Key de DeepSeek lista: https://platform.deepseek.com

---

## Paso 1: Configurar API Key

Edita el archivo `docker-compose.yml` y busca esta línea:
```yaml
DEEPSEEK_API_KEY: "${DEEPSEEK_API_KEY}"
```

Cámbiala a:
```yaml
DEEPSEEK_API_KEY: "sk-tu-api-key-aqui"
```

O crea un archivo `.env` en la raíz del proyecto:
```
DEEPSEEK_API_KEY=sk-tu-api-key-aqui
```

---

## Paso 2: Configurar IPs y Tokens

En `docker-compose.yml`, verifica que estos valores sean correctos:

```yaml
IP_LAPTOP: "172.16.12.100"          # IP de la máquina con el puente
PUERTO_LAPTOP: "9000"               # Puerto del puente
API_TOKEN: "1234567890"             # Debe coincidir con whatsapp-bridge.js
```

---

## Paso 3: Iniciar el Contenedor

### En Windows:
```bash
# Doble click en: start-docker.bat
# O ejecuta en Command Prompt:
docker-compose up -d
```

### En Linux/Mac:
```bash
# Dale permisos de ejecución (primera vez)
chmod +x start-docker.sh

# Ejecuta
./start-docker.sh
# O manualmente:
docker-compose up -d
```

---

## Paso 4: Verificar que Funciona

```bash
# Ver si el contenedor está corriendo
docker-compose ps

# Ver los logs
docker-compose logs

# Hacer un health check
curl http://localhost:8523/health

# Acceder al dashboard
# Abre en el navegador: http://localhost:8523/
```

---

## Paso 5: Verificar Conectividad

Desde el navegador, verifica que:
1. El dashboard carga sin errores
2. Los tickets se listan correctamente
3. Los logs muestran "Conectado a WhatsApp y listo"

---

## Detener el Contenedor

### En Windows:
```bash
# Doble click en: stop-docker.bat
# O:
docker-compose down
```

### En Linux/Mac:
```bash
./stop-docker.sh
# O:
docker-compose down
```

---

## Comandos Útiles

| Comando | Qué hace |
|---------|----------|
| `docker-compose ps` | Ver estado del contenedor |
| `docker-compose logs -f` | Ver logs en vivo |
| `docker-compose logs --tail=50` | Ver últimas 50 líneas |
| `docker-compose restart` | Reiniciar contenedor |
| `docker-compose down` | Detener y remover contenedor |
| `docker-compose build` | Reconstruir imagen |

---

## ⚠️ Troubleshooting Rápido

### "Port 8523 already in use"
```bash
# Cambiar puerto en docker-compose.yml:
ports:
  - "9999:8523"  # Cambiar 9999 al puerto que quieras
```

### "DEEPSEEK_API_KEY is empty"
Asegúrate de:
1. Tener tu API Key configurada en `docker-compose.yml`
2. Reiniciar el contenedor: `docker-compose restart`

### "Cannot connect to whatsapp-bridge"
Verifica:
1. IP_LAPTOP es correcta (donde está el puente)
2. PUERTO_LAPTOP es 9000
3. API_TOKEN coincide en ambos lados
4. La máquina del puente está en red alcanzable

### Ver error específico
```bash
docker-compose logs whatsapp-tickets-api
```

---

## ✅ Checklist Final

- [ ] Docker instalado y funcionando
- [ ] API Key de DeepSeek configurada
- [ ] docker-compose.yml con valores correctos
- [ ] `docker-compose up -d` ejecutado
- [ ] `docker-compose ps` muestra contenedor corriendo
- [ ] `curl http://localhost:8523/health` responde OK
- [ ] Dashboard accesible en http://localhost:8523/
- [ ] Puente WhatsApp conectando

---

## 📞 Si algo falla

1. Lee los logs: `docker-compose logs`
2. Verifica variables: `docker-compose config`
3. Reinicia: `docker-compose restart`
4. Rebuild si hay cambios: `docker-compose build && docker-compose up -d`

---

¡Sistema listo para usar! 🎉
