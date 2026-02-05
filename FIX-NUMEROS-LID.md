# Solución para Números en Formato LID

## ¿Qué es el problema?

WhatsApp introdujo en 2024 un nuevo formato de identificación llamado **LID (Lidded Identity)** que se ve así:
```
257354507501662@lid
```

En lugar del formato tradicional:
```
5214772758198@s.whatsapp.net
```

Esto causaba que en tu sistema se mostraran números con `@lid` en lugar del número telefónico limpio.

## ✅ Solución Implementada

Se realizaron los siguientes cambios:

### 1. whatsapp-bridge.js
- Se agregó la función `extraerNumeroTelefonico()` que convierte automáticamente el formato LID al formato estándar de WhatsApp
- Ahora todos los mensajes recibidos se procesan con el número limpio antes de enviarse al servidor

### 2. main.py  
- Se agregó la función `limpiar_numero_telefono()` que formatea el número para mostrarlo correctamente
- Se aplica automáticamente al guardar nuevos tickets en la base de datos
- Convierte cualquier formato a: `+5214772758198`

### 3. migrar_numeros_lid.py
- Script de migración para limpiar los números que ya están en la base de datos
- Solo necesitas ejecutarlo UNA VEZ

## 📝 Cómo Aplicar la Solución

### Paso 1: Reiniciar el sistema
```bash
# Detener los servicios actuales
.\stop-docker.bat

# O si no usas Docker:
# Detener manualmente los procesos de Python y Node.js
```

### Paso 2: Migrar números existentes
```bash
# Ejecutar el script de migración (solo una vez)
python migrar_numeros_lid.py
```

### Paso 3: Reiniciar servicios
```bash
# Si usas Docker:
.\start-docker.bat

# Si no usas Docker:
# Terminal 1 (Python):
python main.py

# Terminal 2 (Node.js):
node whatsapp-bridge.js
```

## 🔍 Verificación

Después de aplicar los cambios:

1. Los nuevos tickets mostrarán números en formato: `+5214772758198`
2. Los tickets antiguos se habrán actualizado con el formato correcto
3. Ya no verás identificadores como `257354507501662@lid`

## 📚 Referencias Técnicas

**Formatos soportados:**
- `257354507501662@lid` → `+257354507501662`
- `5214772758198@s.whatsapp.net` → `+5214772758198`
- `+5214772758198` → `+5214772758198` (sin cambios)

**Archivos modificados:**
- `whatsapp-bridge.js` - Procesamiento de mensajes entrantes
- `main.py` - Almacenamiento en base de datos
- `migrar_numeros_lid.py` (nuevo) - Script de migración

## ❓ Preguntas Frecuentes

**P: ¿Por qué WhatsApp cambió el formato?**  
R: WhatsApp introdujo LID como parte de sus actualizaciones de privacidad y seguridad en 2024.

**P: ¿Necesito ejecutar la migración cada vez?**  
R: No, solo una vez. Los nuevos tickets ya se guardarán con el formato correcto.

**P: ¿Afecta el envío de mensajes?**  
R: No, el sistema convierte automáticamente entre formatos según sea necesario.
