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
from typing import Optional

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
MAX_IMAGE_SIZE = int(os.getenv("MAX_IMAGE_SIZE", "16000000"))  # 16MB por defecto

if not os.path.exists(CARPETA_FOTOS):
    os.makedirs(CARPETA_FOTOS)

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
            foto_path TEXT
        )
    ''')
    conn.commit()
    conn.close()

init_db()

class MensajeWA(BaseModel):
    remitente: str
    contenido: str
    imagen: Optional[str] = None

def verificar_token(authorization: str = Header(...)):
    """Middleware para verificar el token de autenticación"""
    token = authorization.replace("Bearer ", "")
    if token != API_TOKEN:
        logger.warning(f"Intento de acceso no autorizado con token inválido")
        raise HTTPException(status_code=401, detail="No autorizado")
    return True

def analizar_ia(t):
    t = t.lower()
    if "pantalla" in t or "roto" in t: return "Hardware - Pantalla"
    if "prende" in t or "bateria" in t: return "Hardware - Energía"
    if "lenta" in t or "virus" in t: return "Software - Limpieza"
    return "Soporte General"

@app.get("/")
async def home():
    return FileResponse('index.html')

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
    
    def procesar():
        try:
            path_final = None
            nombre_archivo = None
            if data.imagen:
                nombre = f"img_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
                path_final = os.path.join(CARPETA_FOTOS, nombre)
                nombre_archivo = nombre  # Solo guardar el nombre, no la ruta completa
                with open(path_final, "wb") as f:
                    f.write(base64.b64decode(data.imagen))
                logger.info(f"Imagen guardada: {path_final}")
            
            conn = sqlite3.connect('tickets.db')
            cursor = conn.cursor()
            cursor.execute('INSERT INTO tickets (cliente, descripcion, estado, categoria, fecha, foto_path) VALUES (?,?,?,?,?,?)',
                           (data.remitente, data.contenido, 'Pendiente', analizar_ia(data.contenido), 
                            datetime.datetime.now().strftime("%Y-%m-%d %H:%M"), nombre_archivo))
            ticket_id = cursor.lastrowid
            conn.commit()
            conn.close()
            logger.info(f"Ticket #{ticket_id} creado para {data.remitente}")
        except Exception as e:
            logger.error(f"Error procesando mensaje: {str(e)}")
    
    bg.add_task(procesar)
    return {"status": "ok", "mensaje": "Ticket recibido y procesando"}

@app.get("/tickets")
async def listar():
    conn = sqlite3.connect('tickets.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM tickets ORDER BY id DESC')
    rows = cursor.fetchall()
    conn.close()
    return {"tickets": rows}

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