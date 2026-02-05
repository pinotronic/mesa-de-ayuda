Estrategia: El Microservicio "Puente"
Usaremos Node.js con Baileys para la conexión física con WhatsApp, y este le enviará los mensajes a tu API en FastAPI mediante un Webhook.

1. Instrucciones para crear el "Escuchador" (Node.js + Baileys)
Crea un archivo llamado whatsapp_service.js. Pídele a la IA lo siguiente:

"Escribe un script en Node.js usando la librería @whiskeysockets/baileys que realice lo siguiente:

Inicie una sesión de WhatsApp Multi-Device y muestre el código QR en la terminal para vincularlo.

Mantenga la sesión activa usando un almacenamiento local de credenciales (auth_info).

Implemente un evento de escucha de mensajes (messages.upsert).

Cada vez que llegue un mensaje de texto nuevo, lo envíe mediante una petición HTTP POST a mi servidor local de FastAPI en la dirección http://localhost:8000/webhook.

El JSON enviado debe incluir: numero (quien envía), mensaje (el texto) y timestamp."

2. Instrucciones para tu API de Tickets (Python + FastAPI)
Este es el "cerebro" que mencionamos antes. Pídele a la IA:

"Crea una API con FastAPI en Python que tenga un endpoint llamado /webhook preparado para recibir peticiones POST con un JSON que contenga numero y mensaje.

El script debe validar que el mensaje no esté vacío.

Debe tener una función (placeholder) para guardar este mensaje en una base de datos (puedes usar SQLite por ahora).

Si el mensaje contiene la palabra 'ticket' o 'falla', debe responder con un mensaje de confirmación simulado."

3. Configuración en tu Servidor Local
Para que esto funcione en tus servidores, deberás tener instalado:

Node.js v16+ (Para el escuchador).

Python 3.9+ (Para tu API).

Pasos de ejecución:
Levantar FastAPI: uvicorn main:app --reload --port 8000

Levantar el Puente de WhatsApp: node whatsapp_service.js

Vincular: Escanea el QR que saldrá en la terminal de Node.js con tu celular.


.env servidor

```env
IP_LAPTOP=172.16.76.153
PUERTO_LAPTOP=9000
API_TOKEN=1234567890
MAX_IMAGE_SIZE=16000000
ALLOWED_ORIGINS=*
EOF
```

laptop

```env
# Configuración del WhatsApp Bridge (Laptop)

# URL del servidor donde corre main.py en Docker
# ⚠️ CAMBIAR esta IP por la IP real de tu servidor
SERVER_URL=http://172.16.12.199:8523

# Puerto local donde escucha el puente
PUERTO_LOCAL=9000

# Token compartido para autenticación
# ⚠️ DEBE SER EL MISMO token que configuraste en el servidor Docker (.env del servidor)
API_TOKEN=1234567890
```

