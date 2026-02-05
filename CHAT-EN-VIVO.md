# 💬 Chat en Vivo - Sistema de Tickets

## 📋 Descripción

Se ha implementado un sistema de **chat en vivo** que permite a los técnicos comunicarse directamente con los usuarios desde el panel de tickets, brindando soporte en tiempo real vía WhatsApp.

## ✨ Características

### 🎯 Funcionalidad Principal

- **Chat Interactivo**: Interfaz visual de chat para comunicación directa
- **Historial Completo**: Visualiza toda la conversación con el usuario
- **Envío Instantáneo**: Mensajes enviados directamente a WhatsApp del usuario
- **Auto-actualización**: El chat se actualiza automáticamente cada 5 segundos
- **Identificación Visual**: Los mensajes del técnico se muestran en color verde

### 🎨 Interfaz

#### Botones en la Tabla de Tickets

Cada ticket ahora tiene 3 botones de acción:
- **💬 Chat en Vivo** (Morado) - Abre el chat interactivo
- **📋 Historial** (Azul) - Ver conversación completa (solo lectura)
- **✅ Notificar** (Verde) - Envío de mensaje predefinido

#### Modal de Chat Interactivo

El modal incluye:
- **Encabezado**: Número de ticket, nombre del usuario y teléfono
- **Área de Chat**: Mensajes con íconos identificadores:
  - 👤 Usuario
  - 🤖 Sistema/IA
  - 👨‍💻 Técnico
- **Campo de Texto**: Área para escribir mensajes
- **Botón Enviar**: Envía el mensaje a WhatsApp
- **Atajos de Teclado**:
  - `Enter` - Enviar mensaje
  - `Shift + Enter` - Nueva línea
  - `ESC` - Cerrar modal

## 🔧 Cómo Usar

### Paso 1: Abrir Chat
1. Localiza el ticket en la tabla
2. Haz clic en el botón **💬 Chat en Vivo**
3. Se abrirá el modal con el historial de conversación

### Paso 2: Enviar Mensajes
1. Escribe tu mensaje en el área de texto
2. Presiona `Enter` o haz clic en **📤 Enviar**
3. El mensaje se enviará automáticamente al WhatsApp del usuario
4. El mensaje aparecerá instantáneamente en el chat

### Paso 3: Seguimiento
- El chat se actualiza automáticamente cada 5 segundos
- Los nuevos mensajes del usuario aparecerán automáticamente
- Puedes mantener múltiples chats abiertos (uno a la vez)

## 💾 Persistencia

### Almacenamiento
- Todos los mensajes enviados se guardan en el historial del ticket
- Los mensajes del técnico tienen el rol `"tecnico"` en la base de datos
- El historial completo está disponible en cualquier momento

### Estructura del Mensaje en BD
```json
{
  "role": "tecnico",
  "content": "Mensaje del técnico",
  "timestamp": "2026-02-05T10:30:00"
}
```

## 🌐 Endpoints API

### POST `/ticket/{ticket_id}/enviar-mensaje`

Envía un mensaje del técnico al usuario.

**Request Body:**
```json
{
  "mensaje": "Texto del mensaje"
}
```

**Response (Éxito - 200):**
```json
{
  "status": "enviado",
  "ticket_id": 123,
  "telefono": "+5214772758198",
  "mensaje": "Mensaje enviado correctamente"
}
```

**Errores Posibles:**
- `404` - Ticket no encontrado
- `503` - WhatsApp desconectado (mensaje guardado pero no enviado)
- `504` - Timeout al conectar con WhatsApp
- `500` - Error interno

### GET `/ticket/{ticket_id}/conversacion`

Obtiene el historial completo de la conversación.

**Response:**
```json
{
  "historial": [
    {
      "role": "user",
      "content": "Mi laptop no enciende",
      "timestamp": "2026-02-05T09:00:00"
    },
    {
      "role": "assistant",
      "content": "¿Cuál es tu nombre?",
      "timestamp": "2026-02-05T09:00:01"
    },
    {
      "role": "tecnico",
      "content": "Ya revisamos tu equipo, tiene problema de batería",
      "timestamp": "2026-02-05T10:30:00"
    }
  ]
}
```

## 🔒 Seguridad

- Los mensajes se envían a través del servidor autorizado
- Se valida la existencia del ticket antes de enviar
- Los errores de conexión no impiden guardar el historial
- Logging completo de todas las transacciones

## ⚠️ Manejo de Errores

### WhatsApp Desconectado
Si WhatsApp está desconectado:
1. El mensaje se guarda en el historial del ticket
2. Se muestra un error 503 al técnico
3. El mensaje se puede reenviar automáticamente cuando WhatsApp se reconecte

### Timeout
Si el servidor de WhatsApp no responde:
1. Se muestra error 504
2. El mensaje permanece en el historial
3. Se puede reintentar el envío

## 🎯 Casos de Uso

### Soporte Proactivo
```
Técnico: "Hola Juan, tu laptop ya está lista. Tenía un problema de RAM que ya solucionamos."
```

### Solicitar Información
```
Técnico: "Necesito que me confirmes el número de activo del equipo, no lo veo en la etiqueta"
```

### Actualización de Estado
```
Técnico: "Estamos esperando un repuesto que llega mañana. Te avisamos cuando esté listo."
```

### Diagnóstico Remoto
```
Técnico: "¿Podrías reiniciar el equipo y decirme si aparece algún mensaje de error?"
```

## 📊 Monitoreo

### Logs del Sistema
Todos los mensajes se registran en los logs:
```
INFO - Enviando mensaje del técnico al ticket #123 (+5214772758198)
INFO - Mensaje enviado exitosamente a +5214772758198
```

### Verificación
Puedes verificar que el mensaje se envió:
1. Revisando los logs del servidor
2. Confirmando con el usuario vía WhatsApp
3. Revisando el historial del ticket

## 🚀 Mejoras Futuras Posibles

- [ ] Notificaciones push cuando llega respuesta del usuario
- [ ] Indicador de "escribiendo..."
- [ ] Soporte para envío de imágenes desde el técnico
- [ ] Plantillas de mensajes rápidos
- [ ] Chat grupal con múltiples técnicos
- [ ] Historial de conversaciones por usuario (todos sus tickets)
- [ ] Estadísticas de tiempo de respuesta

## 📝 Notas Técnicas

### Auto-actualización
El chat se actualiza cada 5 segundos usando `setInterval`:
```javascript
intervalActualizacionChat = setInterval(cargarMensajesChat, 5000);
```

### Scroll Automático
El chat hace scroll automático al final solo si el usuario estaba viendo los últimos mensajes:
```javascript
if (scrollAntes < 150) {
    container.scrollTop = container.scrollHeight;
}
```

### Colores de Mensajes
- **Usuario**: Azul (`#3b82f6`)
- **Sistema/IA**: Gris oscuro (`#475569`)
- **Técnico**: Verde (`#059669`)

## ❓ Preguntas Frecuentes

**P: ¿Puedo tener varios chats abiertos al mismo tiempo?**  
R: Puedes abrir un chat a la vez. Si abres otro, el anterior se cierra automáticamente.

**P: ¿Qué pasa si WhatsApp se desconecta mientras envío un mensaje?**  
R: El mensaje se guarda en el historial pero no se envía. Recibirás un error 503 indicándote que reconectes WhatsApp.

**P: ¿El usuario verá quién le envía el mensaje?**  
R: El usuario recibirá el mensaje desde el número de WhatsApp conectado al sistema.

**P: ¿Se guarda el historial de chat?**  
R: Sí, todo el historial se guarda en la base de datos del ticket y está disponible permanentemente.

**P: ¿Puedo enviar emojis o caracteres especiales?**  
R: Sí, el sistema soporta UTF-8 completo, incluyendo emojis y caracteres especiales.

---

**Desarrollado para mejorar la experiencia de soporte técnico** ✨
