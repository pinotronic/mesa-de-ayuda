const { default: makeWASocket, useMultiFileAuthState, downloadContentFromMessage } = require('@whiskeysockets/baileys');
const qrcode = require('qrcode-terminal');
const axios = require('axios');
const express = require('express');
const fs = require('fs');
const path = require('path');
require('dotenv').config();

// --- CONFIGURACIÓN ---
const SERVER_URL = process.env.SERVER_URL || 'http://172.16.12.199:8523';
const API_TOKEN = process.env.API_TOKEN || 'cambiar-en-produccion';
const PUERTO_LOCAL = process.env.PUERTO_LOCAL || 9000;
const MAX_REINTENTOS = 3;
const CARPETA_COLA = 'cola_mensajes';

if (!fs.existsSync(CARPETA_COLA)) {
    fs.mkdirSync(CARPETA_COLA, { recursive: true });
}

const app = express();
app.use(express.json({ limit: '50mb' }));

// Variable de estado de conexión
let whatsappConectado = false;
let sock = null;

// --- UTILIDADES ---
function log(mensaje, tipo = 'INFO') {
    const timestamp = new Date().toISOString();
    const emojis = { INFO: 'ℹ️', SUCCESS: '✅', ERROR: '❌', WARNING: '⚠️' };
    console.log(`[${timestamp}] ${emojis[tipo] || 'ℹ️'} ${mensaje}`);
}

async function enviarConReintentos(datos, intento = 1) {
    try {
        await axios.post(`${SERVER_URL}/webhook`, datos, {
            headers: { 'Authorization': `Bearer ${API_TOKEN}` },
            timeout: 5000
        });
        log(`Mensaje enviado al servidor (intento ${intento})`, 'SUCCESS');
        return true;
    } catch (error) {
        log(`Error en intento ${intento}: ${error.message}`, 'ERROR');
        
        if (intento < MAX_REINTENTOS) {
            const espera = Math.pow(2, intento) * 1000; // Backoff exponencial
            log(`Reintentando en ${espera/1000}s...`, 'WARNING');
            await new Promise(resolve => setTimeout(resolve, espera));
            return enviarConReintentos(datos, intento + 1);
        } else {
            // Guardar en cola local
            const nombreArchivo = `msg_${Date.now()}.json`;
            const rutaArchivo = path.join(CARPETA_COLA, nombreArchivo);
            fs.writeFileSync(rutaArchivo, JSON.stringify(datos));
            log(`Mensaje guardado en cola local: ${nombreArchivo}`, 'WARNING');
            return false;
        }
    }
}

async function procesarCola() {
    const archivos = fs.readdirSync(CARPETA_COLA);
    if (archivos.length === 0) return;
    
    log(`Procesando ${archivos.length} mensajes pendientes...`, 'INFO');
    
    for (const archivo of archivos) {
        const rutaArchivo = path.join(CARPETA_COLA, archivo);
        try {
            const datos = JSON.parse(fs.readFileSync(rutaArchivo, 'utf8'));
            const enviado = await enviarConReintentos(datos);
            if (enviado) {
                fs.unlinkSync(rutaArchivo);
                log(`Mensaje de cola procesado: ${archivo}`, 'SUCCESS');
            }
        } catch (error) {
            log(`Error procesando cola ${archivo}: ${error.message}`, 'ERROR');
        }
    }
}

// Procesar cola cada 2 minutos
setInterval(procesarCola, 120000);

async function iniciar() {
    const { state, saveCreds } = await useMultiFileAuthState('sesion_wa');
    sock = makeWASocket({ 
        auth: state,
        printQRInTerminal: false  // Deshabilitado, manejamos manualmente
    });

    sock.ev.on('creds.update', saveCreds);
    sock.ev.on('connection.update', (up) => {
        const { connection, lastDisconnect, qr } = up;
        
        // Mostrar QR cuando esté disponible
        if (qr) {
            console.log('\n📱 Escanea este código QR con WhatsApp:\n');
            qrcode.generate(qr, { small: true });
            log('Código QR generado. Escanéalo con tu teléfono.', 'INFO');
        }
        
        if (connection === 'open') {
            whatsappConectado = true;
            log('Conectado a WhatsApp y listo', 'SUCCESS');
            procesarCola(); // Procesar mensajes pendientes al conectar
        }
        
        if (connection === 'close') {
            whatsappConectado = false;
            const shouldReconnect = lastDisconnect?.error?.output?.statusCode !== 401;
            log(`Conexión a WhatsApp cerrada. Reconectar: ${shouldReconnect}`, 'WARNING');
            
            if (shouldReconnect) {
                log('Reintentando conexión en 5 segundos...', 'INFO');
                setTimeout(() => iniciar(), 5000);
            } else {
                log('Sesión cerrada por WhatsApp. Elimina sesion_wa/ y reinicia.', 'ERROR');
            }
        }
    });

    sock.ev.on('messages.upsert', async ({ messages }) => {
        const m = messages[0];
        if (!m.message || m.key.fromMe) return;

        const tipo = Object.keys(m.message)[0];
        let texto = m.message.conversation || m.message.extendedTextMessage?.text || "";
        let imgB64 = null;

        if (tipo === 'imageMessage') {
            texto = m.message.imageMessage.caption || "Imagen enviada";
            try {
                const stream = await downloadContentFromMessage(m.message.imageMessage, 'image');
                let buffer = Buffer.from([]);
                for await (const chunk of stream) { buffer = Buffer.concat([buffer, chunk]); }
                
                // Validar tamaño (máx 16MB)
                if (buffer.length > 16_000_000) {
                    log('Imagen muy grande, descartando', 'WARNING');
                    imgB64 = null;
                    texto += " [Imagen muy grande, no procesada]";
                } else {
                    imgB64 = buffer.toString('base64');
                }
            } catch (error) {
                log(`Error descargando imagen: ${error.message}`, 'ERROR');
            }
        }

        if (texto || imgB64) {
            await enviarConReintentos({
                remitente: m.key.remoteJid,
                contenido: texto,
                imagen: imgB64
            });
        }
    });

    // Middleware de autenticación
    const verificarToken = (req, res, next) => {
        const token = req.headers['authorization']?.replace('Bearer ', '');
        if (token !== API_TOKEN) {
            return res.status(401).json({ error: 'No autorizado' });
        }
        next();
    };

    app.post('/enviar-mensaje', verificarToken, async (req, res) => {
        try {
            const { numero, texto } = req.body;
            
            if (!numero || !texto) {
                return res.status(400).json({ error: 'Faltan parámetros' });
            }
            
            // Verificar conexión de WhatsApp antes de enviar
            if (!whatsappConectado || !sock) {
                log('WhatsApp desconectado, no se puede enviar mensaje', 'ERROR');
                return res.status(503).json({ 
                    error: 'WhatsApp desconectado',
                    solucion: 'Reconecta WhatsApp escaneando el código QR'
                });
            }
            
            await sock.sendMessage(numero, { text: texto });
            log(`Mensaje enviado a ${numero}`, 'SUCCESS');
            res.json({ ok: true, mensaje: 'Enviado correctamente' });
        } catch (error) {
            log(`Error enviando mensaje: ${error.message}`, 'ERROR');
            res.status(500).json({ error: error.message });
        }
    });

    app.get('/health', (req, res) => {
        const estado = whatsappConectado ? 'conectado' : 'desconectado';
        res.json({
            status: 'ok',
            whatsapp: estado,
            cola_pendiente: fs.readdirSync(CARPETA_COLA).length,
            uptime: process.uptime()
        });
    });
}

app.listen(PUERTO_LOCAL, () => {
    log(`Puente escuchando en puerto ${PUERTO_LOCAL}`, 'SUCCESS');
    log(`Servidor configurado: ${SERVER_URL}`, 'INFO');
});

iniciar();