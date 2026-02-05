"""
Script para limpiar números telefónicos en formato LID de la base de datos.
Ejecuta este script UNA VEZ después de actualizar el código.

Convierte: 257354507501662@lid -> +257354507501662
Convierte: 5214772758198@s.whatsapp.net -> +5214772758198
"""

import sqlite3

def limpiar_numero_telefono(numero: str) -> str:
    """
    Limpia el número telefónico del formato JID de WhatsApp (LID o tradicional).
    """
    if not numero:
        return numero
    
    # Extraer solo el número antes del @
    if '@' in numero:
        numero = numero.split('@')[0]
    
    # Agregar + al inicio si no lo tiene
    if not numero.startswith('+'):
        numero = '+' + numero
    
    return numero

def migrar_numeros():
    """Actualiza todos los números en la base de datos"""
    conn = sqlite3.connect('tickets.db')
    cursor = conn.cursor()
    
    # Obtener todos los tickets
    cursor.execute('SELECT id, cliente FROM tickets')
    tickets = cursor.fetchall()
    
    actualizados = 0
    for ticket_id, cliente in tickets:
        # Solo actualizar si tiene formato LID o WhatsApp JID
        if cliente and ('@lid' in cliente or '@s.whatsapp.net' in cliente):
            numero_limpio = limpiar_numero_telefono(cliente)
            cursor.execute('UPDATE tickets SET cliente = ? WHERE id = ?', (numero_limpio, ticket_id))
            print(f"✅ Ticket #{ticket_id}: {cliente} -> {numero_limpio}")
            actualizados += 1
    
    conn.commit()
    conn.close()
    
    print(f"\n✨ Migración completada: {actualizados} números actualizados")

if __name__ == "__main__":
    print("🔧 Iniciando migración de números telefónicos...\n")
    migrar_numeros()
    print("\n✅ ¡Listo! Los números ahora se mostrarán correctamente.")
