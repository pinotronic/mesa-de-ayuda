from fastapi import FastAPI, BackgroundTasks, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import sqlite3
import datetime
import requests
import os
import base64
import logging
import json
import asyncio
import aiohttp
from typing import Optional
from dotenv import load_dotenv

load_dotenv()

# --- CONFIGURACIÓN DE LOGGING ---
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI(title="Sistema de Tickets WhatsApp")

# --- CONFIGURACIÓN DESDE VARIABLES DE ENTORNO ---
IP_LAPTOP = os.getenv("IP_LAPTOP", "172.16.12.100")
PUERTO_LAPTOP = os.getenv("PUERTO_LAPTOP", "9000")
API_TOKEN = os.getenv("API_TOKEN", "cambiar-en-produccion")
CARPETA_FOTOS = os.getenv("CARPETA_FOTOS", "fotos_evidencia")
CARPETA_LOGS = os.getenv("CARPETA_LOGS", "logs_conversaciones")
MAX_IMAGE_SIZE = int(os.getenv("MAX_IMAGE_SIZE", "16000000"))  # 16MB por defecto
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")
DEEPSEEK_MODEL = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")
DEEPSEEK_MAX_TOKENS = int(os.getenv("DEEPSEEK_MAX_TOKENS", "2000"))
SESSION_TIMEOUT_MINUTES = int(os.getenv("SESSION_TIMEOUT_MINUTES", "15"))

if not os.path.exists(CARPETA_FOTOS):
    os.makedirs(CARPETA_FOTOS)

if not os.path.exists(CARPETA_LOGS):
    os.makedirs(CARPETA_LOGS)

# CORS más restrictivo - ajustar según necesidades
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "*").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_methods=["GET", "POST"],
    allow_headers=["*"]
)

app.mount("/fotos", StaticFiles(directory=CARPETA_FOTOS), name="fotos")

# --- BASE DE DATOS ---
def init_db():
    conn = sqlite3.connect('tickets.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tickets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cliente TEXT,
            descripcion TEXT,
            estado TEXT,
            categoria TEXT,
            fecha TEXT,
            foto_path TEXT,
            nombre_usuario TEXT,
            departamento TEXT,
            tipo_equipo TEXT,
            numero_activo TEXT,
            falla_detallada TEXT,
            diagnostico_ia TEXT,
            requiere_tecnico INTEGER,
            estado_conversacion TEXT,
            historial_conversacion TEXT,
            log_file_path TEXT
        )
    ''')

    # Agregar columnas nuevas si no existen (migración para BD existentes)
    cursor.execute("PRAGMA table_info(tickets)")
    columnas_existentes = [col[1] for col in cursor.fetchall()]

    columnas_nuevas = {
        'nombre_usuario': 'TEXT',
        'departamento': 'TEXT',
        'tipo_equipo': 'TEXT',
        'numero_activo': 'TEXT',
        'falla_detallada': 'TEXT',
        'diagnostico_ia': 'TEXT',
        'requiere_tecnico': 'INTEGER',
        'estado_conversacion': 'TEXT',
        'historial_conversacion': 'TEXT',
        'log_file_path': 'TEXT'
    }

    for columna, tipo in columnas_nuevas.items():
        if columna not in columnas_existentes:
            try:
                cursor.execute(f'ALTER TABLE tickets ADD COLUMN {columna} {tipo}')
                logger.info(f"Columna {columna} agregada a la tabla tickets")
            except sqlite3.OperationalError as e:
                logger.warning(f"Columna {columna} ya existe: {e}")

    conn.commit()
    conn.close()

init_db()

class MensajeWA(BaseModel):
    remitente: str
    contenido: str
    imagen: Optional[str] = None

# --- CLASES DE CONVERSACIÓN ---
class ConversationSession:
    ESTADOS = ["INICIO", "NOMBRE", "DEPTO", "EQUIPO", "ACTIVO", "FALLA", "DIAGNOSTICO", "FINALIZADO"]

    def __init__(self, remitente: str):
        self.remitente = remitente
        self.estado = "INICIO"
        self.datos = {}
        self.historial = []
        self.ultimo_mensaje = datetime.datetime.now()
        self.ticket_id = None

    def esta_expirada(self, timeout_minutes: int = 15) -> bool:
        delta = datetime.datetime.now() - self.ultimo_mensaje
        return delta.total_seconds() > (timeout_minutes * 60)


class ConversationManager:
    def __init__(self):
        self.sesiones = {}

    def get_session(self, remitente: str) -> Optional[ConversationSession]:
        if remitente in self.sesiones:
            sesion = self.sesiones[remitente]
            if sesion.esta_expirada(SESSION_TIMEOUT_MINUTES):
                logger.info(f"Sesión expirada para {remitente}")
                del self.sesiones[remitente]
                return None
            return sesion
        return None

    def create_session(self, remitente: str) -> ConversationSession:
        sesion = ConversationSession(remitente)
        self.sesiones[remitente] = sesion
        logger.info(f"Nueva sesión creada para {remitente}")
        return sesion

    def end_session(self, remitente: str):
        if remitente in self.sesiones:
            del self.sesiones[remitente]
            logger.info(f"Sesión finalizada para {remitente}")

    def cleanup_expired_sessions(self, timeout_minutes: int = 15):
        remitentes_expirados = []
        for remitente, sesion in self.sesiones.items():
            if sesion.esta_expirada(timeout_minutes):
                remitentes_expirados.append(remitente)

        for remitente in remitentes_expirados:
            logger.warning(f"Sesión expirada y limpiada: {remitente}")
            del self.sesiones[remitente]


# --- CLIENTE DEEPSEEK ---
class DeepSeekClient:
    def __init__(self, api_key: str, model: str = "deepseek-chat"):
        self.api_key = api_key
        self.model = model
        self.base_url = "https://api.deepseek.com/v1"

    async def diagnosticar_problema(self, tipo_equipo: str, falla_desc: str, historial: list) -> dict:
        """Analiza el problema y sugiere soluciones usando DeepSeek"""
        if not self.api_key:
            logger.warning("API Key de DeepSeek no configurada")
            return {
                "analisis": "No se pudo realizar análisis (API no configurada)",
                "sugerencias": "Por favor, contacta al soporte técnico.",
                "requiere_tecnico": True
            }

        sistema_prompt = f"""Eres un asistente de soporte técnico experto. Un usuario reporta un problema en su equipo.

EQUIPAMIENTO: {tipo_equipo}
DESCRIPCIÓN DE LA FALLA: {falla_desc}

Analiza el problema y:
1. Proporciona 2-3 pasos de diagnóstico que el usuario puede seguir
2. Determina si es probable que requiera intervención técnica presencial
3. Sé conciso pero profesional

Responde en formato JSON con estructura:
{{"pasos": ["paso 1", "paso 2", "paso 3"], "requiere_tecnico": true/false, "urgencia": "alta"/"media"/"baja"}}"""

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_url}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": self.model,
                        "messages": [
                            {"role": "system", "content": sistema_prompt},
                            {"role": "user", "content": "Analiza el problema"}
                        ],
                        "max_tokens": DEEPSEEK_MAX_TOKENS,
                        "temperature": 0.7
                    },
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as resp:
                    if resp.status != 200:
                        logger.error(f"Error DeepSeek: {resp.status}")
                        return {
                            "analisis": "Error al conectar con el servicio de IA",
                            "sugerencias": "Por favor, intenta nuevamente",
                            "requiere_tecnico": True
                        }

                    data = await resp.json()
                    respuesta = data['choices'][0]['message']['content']

                    try:
                        resultado = json.loads(respuesta)
                        pasos = "\n".join([f"• {paso}" for paso in resultado.get("pasos", [])])
                        requiere_tecnico = resultado.get("requiere_tecnico", True)

                        return {
                            "analisis": f"Pasos de diagnóstico:\n{pasos}",
                            "sugerencias": f"Pasos de diagnóstico:\n{pasos}",
                            "requiere_tecnico": requiere_tecnico
                        }
                    except json.JSONDecodeError:
                        # Si no es JSON válido, parsear la respuesta como texto
                        return {
                            "analisis": respuesta,
                            "sugerencias": respuesta,
                            "requiere_tecnico": True
                        }

        except Exception as e:
            logger.error(f"Error en DeepSeek: {str(e)}")
            return {
                "analisis": f"Error: {str(e)}",
                "sugerencias": "Por favor, contacta al soporte técnico.",
                "requiere_tecnico": True
            }


def verificar_token(authorization: str = Header(...)):
    """Middleware para verificar el token de autenticación"""
    token = authorization.replace("Bearer ", "")
    if token != API_TOKEN:
        logger.warning(f"Intento de acceso no autorizado con token inválido")
        raise HTTPException(status_code=401, detail="No autorizado")
    return True

# --- INSTANCIAS GLOBALES ---
conversation_manager = ConversationManager()
deepseek_client = DeepSeekClient(DEEPSEEK_API_KEY) if DEEPSEEK_API_KEY else None

# --- FUNCIONES AUXILIARES ---
def guardar_log_conversacion(ticket_id: int, sesion: ConversationSession) -> str:
    """Guarda el historial de conversación en un archivo .log"""
    os.makedirs(CARPETA_LOGS, exist_ok=True)

    filename = f"ticket_{ticket_id:03d}_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    filepath = os.path.join(CARPETA_LOGS, filename)

    with open(filepath, 'w', encoding='utf-8') as f:
        for msg in sesion.historial:
            role = "USUARIO" if msg['role'] == 'user' else "SISTEMA"
            timestamp = msg.get('timestamp', datetime.datetime.now().isoformat())
            f.write(f"[{timestamp}] {role}: {msg['content']}\n")

    logger.info(f"Log guardado: {filepath}")
    return filename


def guardar_ticket(sesion: ConversationSession) -> int:
    """Guarda el ticket completo en la BD"""
    conn = sqlite3.connect('tickets.db')
    cursor = conn.cursor()

    historial_json = json.dumps(sesion.historial, ensure_ascii=False, indent=2)

    cursor.execute('''
        INSERT INTO tickets (
            cliente, nombre_usuario, departamento, tipo_equipo, numero_activo,
            descripcion, falla_detallada, estado, categoria, fecha, estado_conversacion,
            diagnostico_ia, requiere_tecnico, historial_conversacion
        ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)
    ''', (
        sesion.remitente,
        sesion.datos.get('nombre', ''),
        sesion.datos.get('departamento', ''),
        sesion.datos.get('tipo_equipo', ''),
        sesion.datos.get('numero_activo', ''),
        sesion.datos.get('falla', '')[:500],  # Resumen en descripcion
        sesion.datos.get('falla', ''),
        'Pendiente',
        sesion.datos.get('categoria', 'Soporte General'),
        datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
        'completo',
        sesion.datos.get('diagnostico', ''),
        1 if sesion.datos.get('requiere_tecnico', False) else 0,
        historial_json
    ))

    ticket_id = cursor.lastrowid
    conn.commit()
    conn.close()

    return ticket_id


def categorizar_falla(tipo_equipo: str, falla: str) -> str:
    """Categoriza la falla según tipo de equipo y descripción"""
    falla_lower = falla.lower()

    if tipo_equipo.lower() in ['desktop', 'laptop']:
        if any(x in falla_lower for x in ['pantalla', 'roto', 'monitor']):
            return "Hardware - Pantalla"
        elif any(x in falla_lower for x in ['prende', 'bateria', 'poder']):
            return "Hardware - Energía"
        elif any(x in falla_lower for x in ['lenta', 'lento', 'virus', 'malware']):
            return "Software"
        elif any(x in falla_lower for x in ['internet', 'conexion', 'wifi']):
            return "Conectividad"
    elif tipo_equipo.lower() == 'impresora':
        if any(x in falla_lower for x in ['papel', 'atasco', 'atasca']):
            return "Hardware - Papel"
        elif any(x in falla_lower for x in ['no imprime', 'tinta', 'cartucho']):
            return "Hardware - Consumibles"

    return "Soporte General"


async def enviar_respuesta_whatsapp(numero: str, texto: str):
    """Envía una respuesta al usuario vía WhatsApp"""
    try:
        response = requests.post(
            f"http://{IP_LAPTOP}:{PUERTO_LAPTOP}/enviar-mensaje",
            json={"numero": numero, "texto": texto},
            headers={"Authorization": f"Bearer {API_TOKEN}"},
            timeout=5
        )
        response.raise_for_status()
        logger.info(f"Respuesta enviada a {numero}")
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 503:
            logger.warning(f"WhatsApp desconectado, no se pudo enviar mensaje a {numero}")
        else:
            logger.error(f"Error HTTP enviando respuesta a {numero}: {e.response.status_code} - {e.response.text}")
    except Exception as e:
        logger.error(f"Error enviando respuesta a {numero}: {str(e)}")


# Limpieza periódica de sesiones expiradas
async def limpiar_sesiones_expiradas():
    """Ejecutar limpieza cada 5 minutos"""
    while True:
        await asyncio.sleep(300)
        conversation_manager.cleanup_expired_sessions(SESSION_TIMEOUT_MINUTES)


@app.on_event("startup")
async def startup_event():
    asyncio.create_task(limpiar_sesiones_expiradas())

@app.get("/health")
async def health():
    """Endpoint de health check para monitoreo"""
    try:
        conn = sqlite3.connect('tickets.db')
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM tickets')
        total_tickets = cursor.fetchone()[0]
        conn.close()
        
        return JSONResponse({
            "status": "ok",
            "total_tickets": total_tickets,
            "laptop_url": f"http://{IP_LAPTOP}:{PUERTO_LAPTOP}",
            "timestamp": datetime.datetime.now().isoformat()
        })
    except Exception as e:
        logger.error(f"Error en health check: {str(e)}")
        return JSONResponse(
            status_code=503,
            content={"status": "error", "message": str(e)}
        )

@app.post("/webhook")
async def recibir(data: MensajeWA, bg: BackgroundTasks, authorization: str = Header(None)):
    # Verificar autenticación
    if not authorization:
        logger.warning("Intento de acceso sin token")
        raise HTTPException(status_code=401, detail="No autorizado - Token faltante")

    try:
        verificar_token(authorization)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error validando token: {str(e)}")
        raise HTTPException(status_code=401, detail="No autorizado")

    # Validar tamaño de imagen
    if data.imagen:
        try:
            img_size = len(base64.b64decode(data.imagen))
            if img_size > MAX_IMAGE_SIZE:
                logger.warning(f"Imagen muy grande recibida: {img_size} bytes")
                raise HTTPException(status_code=413, detail=f"Imagen muy grande. Máximo {MAX_IMAGE_SIZE/1_000_000}MB")
        except Exception as e:
            if isinstance(e, HTTPException):
                raise
            logger.error(f"Error decodificando imagen: {str(e)}")
            raise HTTPException(status_code=400, detail="Imagen inválida")

    async def procesar_conversacion():
        """Maneja la lógica de conversación interactiva"""
        try:
            # Verificar si existe sesión activa
            sesion = conversation_manager.get_session(data.remitente)

            respuesta = ""
            imagen_guardada = None

            # Guardar imagen si viene
            if data.imagen:
                try:
                    nombre = f"img_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
                    path_final = os.path.join(CARPETA_FOTOS, nombre)
                    with open(path_final, "wb") as f:
                        f.write(base64.b64decode(data.imagen))
                    imagen_guardada = nombre
                    logger.info(f"Imagen guardada: {path_final}")
                except Exception as e:
                    logger.error(f"Error guardando imagen: {str(e)}")

            if not sesion:
                # NUEVA SESIÓN - INICIO
                sesion = conversation_manager.create_session(data.remitente)
                respuesta = "¡Hola! 👋 Soy el asistente de soporte técnico.\n\n¿Cuál es tu nombre completo por favor?"
                sesion.estado = "NOMBRE"

            elif sesion.estado == "NOMBRE":
                # Guardar nombre y pedir departamento
                sesion.datos['nombre'] = data.contenido.strip()
                respuesta = f"Gracias {sesion.datos['nombre']}. ¿A qué departamento perteneces?"
                sesion.estado = "DEPTO"

            elif sesion.estado == "DEPTO":
                # Guardar departamento y pedir tipo de equipo
                sesion.datos['departamento'] = data.contenido.strip()
                respuesta = "¿Qué tipo de equipo tiene el problema?\n(Desktop / Laptop / Impresora / Otro)"
                sesion.estado = "EQUIPO"

            elif sesion.estado == "EQUIPO":
                # Guardar tipo de equipo y pedir activo
                sesion.datos['tipo_equipo'] = data.contenido.strip()
                respuesta = "¿Cuál es el número de activo del equipo? (Suele estar en una etiqueta)"
                sesion.estado = "ACTIVO"

            elif sesion.estado == "ACTIVO":
                # Guardar activo y pedir descripción de falla
                sesion.datos['numero_activo'] = data.contenido.strip()
                respuesta = "Perfecto. Ahora, describe detalladamente el problema que estás experimentando."
                sesion.estado = "FALLA"

            elif sesion.estado == "FALLA":
                # Guardar falla, diagnosticar con IA y crear ticket
                sesion.datos['falla'] = data.contenido.strip()
                sesion.datos['categoria'] = categorizar_falla(
                    sesion.datos.get('tipo_equipo', ''),
                    sesion.datos['falla']
                )

                # Llamar a DeepSeek para diagnóstico
                diagnostico = {}
                if deepseek_client:
                    logger.info(f"Solicitando diagnóstico a DeepSeek para {data.remitente}")
                    diagnostico = await deepseek_client.diagnosticar_problema(
                        sesion.datos['tipo_equipo'],
                        sesion.datos['falla'],
                        sesion.historial
                    )
                else:
                    diagnostico = {
                        "analisis": "Análisis de IA no disponible",
                        "sugerencias": "Por favor contacta al soporte técnico",
                        "requiere_tecnico": True
                    }

                sesion.datos['diagnostico'] = diagnostico.get('sugerencias', '')
                sesion.datos['requiere_tecnico'] = diagnostico.get('requiere_tecnico', True)

                # Construir respuesta
                respuesta = f"📋 *Análisis del problema:*\n\n{diagnostico.get('sugerencias', 'Error en análisis')}\n\n"

                if sesion.datos['requiere_tecnico']:
                    respuesta += "Se ha creado un ticket. Un técnico te contactará pronto. ✅"
                    # Crear ticket inmediatamente
                    ticket_id = guardar_ticket(sesion)
                    log_filename = guardar_log_conversacion(ticket_id, sesion)

                    conn = sqlite3.connect('tickets.db')
                    cursor = conn.cursor()
                    cursor.execute('UPDATE tickets SET log_file_path=?, foto_path=? WHERE id=?',
                                   (log_filename, imagen_guardada, ticket_id))
                    conn.commit()
                    conn.close()

                    conversation_manager.end_session(data.remitente)
                else:
                    respuesta += "Intenta estos pasos. Si el problema persiste, responde con 'NO' para hablar con un técnico."
                    sesion.estado = "DIAGNOSTICO"

            elif sesion.estado == "DIAGNOSTICO":
                # Usuario indica si necesita técnico o no
                if "no" in data.contenido.lower() or "no funciona" in data.contenido.lower():
                    # Crear ticket
                    ticket_id = guardar_ticket(sesion)
                    log_filename = guardar_log_conversacion(ticket_id, sesion)

                    conn = sqlite3.connect('tickets.db')
                    cursor = conn.cursor()
                    cursor.execute('UPDATE tickets SET log_file_path=?, foto_path=? WHERE id=?',
                                   (log_filename, imagen_guardada, ticket_id))
                    conn.commit()
                    conn.close()

                    respuesta = f"✅ Ticket #{ticket_id} creado. Un técnico se pondrá en contacto pronto."
                    conversation_manager.end_session(data.remitente)
                else:
                    respuesta = "Me alegra haber ayudado. Si necesitas más ayuda en el futuro, solo envíame un mensaje. 😊"
                    conversation_manager.end_session(data.remitente)

            # Actualizar historial
            sesion.historial.append({
                'timestamp': datetime.datetime.now().isoformat(),
                'role': 'user',
                'content': data.contenido
            })
            sesion.historial.append({
                'timestamp': datetime.datetime.now().isoformat(),
                'role': 'assistant',
                'content': respuesta
            })
            sesion.ultimo_mensaje = datetime.datetime.now()

            # Enviar respuesta al usuario
            await enviar_respuesta_whatsapp(data.remitente, respuesta)

        except Exception as e:
            logger.error(f"Error en procesamiento de conversación: {str(e)}")
            await enviar_respuesta_whatsapp(
                data.remitente,
                "Disculpa, ocurrió un error. Por favor intenta nuevamente."
            )

    bg.add_task(procesar_conversacion)
    return {"status": "ok", "mensaje": "Mensaje procesado"}

@app.get("/")
async def home():
    return FileResponse('index.html')


@app.get("/tickets")
async def listar():
    conn = sqlite3.connect('tickets.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM tickets ORDER BY id DESC')
    rows = cursor.fetchall()
    conn.close()
    return {"tickets": rows}


@app.get("/ticket/{ticket_id}/conversacion")
async def obtener_conversacion(ticket_id: int):
    """Retorna el historial de conversación de un ticket"""
    conn = sqlite3.connect('tickets.db')
    cursor = conn.cursor()
    cursor.execute('SELECT historial_conversacion FROM tickets WHERE id=?', (ticket_id,))
    row = cursor.fetchone()
    conn.close()

    if not row or not row[0]:
        raise HTTPException(status_code=404, detail="Conversación no encontrada")

    try:
        historial = json.loads(row[0])
        return {"historial": historial}
    except json.JSONDecodeError:
        raise HTTPException(status_code=500, detail="Error parseando conversación")


@app.get("/ticket/{ticket_id}/log")
async def descargar_log(ticket_id: int):
    """Descarga el archivo .log de la conversación"""
    conn = sqlite3.connect('tickets.db')
    cursor = conn.cursor()
    cursor.execute('SELECT log_file_path FROM tickets WHERE id=?', (ticket_id,))
    row = cursor.fetchone()
    conn.close()

    if not row or not row[0]:
        raise HTTPException(status_code=404, detail="Log no encontrado")

    log_path = os.path.join(CARPETA_LOGS, row[0])
    if not os.path.exists(log_path):
        raise HTTPException(status_code=404, detail="Archivo de log no existe")

    return FileResponse(log_path, filename=row[0])

@app.post("/responder/{t_id}")
async def responder(t_id: int):
    try:
        conn = sqlite3.connect('tickets.db')
        cursor = conn.cursor()
        cursor.execute('SELECT cliente FROM tickets WHERE id=?', (t_id,))
        row = cursor.fetchone()
        conn.close()
        
        if not row:
            raise HTTPException(status_code=404, detail="Ticket no encontrado")
        
        msg = "Hola, recibimos tu equipo. Estamos trabajando en el diagnóstico. Te avisaremos pronto."
        
        try:
            response = requests.post(
                f"http://{IP_LAPTOP}:{PUERTO_LAPTOP}/enviar-mensaje",
                json={"numero": row[0], "texto": msg},
                headers={"Authorization": f"Bearer {API_TOKEN}"},
                timeout=5
            )
            response.raise_for_status()
            logger.info(f"Mensaje enviado para ticket #{t_id}")
            return {"status": "Enviado", "ticket_id": t_id}
        except requests.exceptions.Timeout:
            logger.error(f"Timeout al enviar mensaje para ticket #{t_id}")
            raise HTTPException(status_code=504, detail="Laptop no responde (timeout)")
        except requests.exceptions.ConnectionError:
            logger.error(f"Laptop desconectada para ticket #{t_id}")
            raise HTTPException(status_code=503, detail="Laptop desconectada")
        except Exception as e:
            logger.error(f"Error enviando mensaje: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Error: {str(e)}")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error en responder: {str(e)}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8523)