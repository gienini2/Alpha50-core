import os
import requests  # <--- FALTABA ESTO
from flask import Flask, request, jsonify
from datetime import datetime
import firebase_admin
from firebase_admin import credentials, db

# Esto es lo que usaremos para que yo RECUERDE tus 92,1 kg
cred = credentials.Certificate("alpha50-fcc77-firebase-adminsdk-fbsvc-a9f291f3ef.json")
firebase_admin.initialize_app(cred, {
    'databaseURL': 'https://alpha50-fcc77-default-rtdb.europe-west1.firebasedatabase.app'
})

def guardar_progreso(usuario, peso, estado):
    ref = db.reference(f'/usuarios/{usuario}/progreso')
    ref.push({
        'fecha': '2026-01-26',
        'peso': peso,
        'estado_intestino': estado
    })
app = Flask(__name__)

# Configuración desde variables de entorno
TOKEN = os.environ.get("TELEGRAM_TOKEN")
CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

def enviar_a_telegram(mensaje):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": mensaje}
    try:
        r = requests.post(url, json=payload)
        return r.text
    except Exception as e:
        return str(e)

@app.route('/', methods=['GET', 'POST'])
def alpha50_webhook():
    # Enviamos un mensaje automático al entrar para confirmar que rula
    enviar_a_telegram("🚀 Alpha50-Core detectado: Servidor Online y vinculado.")
    return "Alpha50 Health Monitor Online - Mensaje de prueba enviado a Telegram."

@app.route('/test')
def test_bot():
    res = enviar_a_telegram("🎯 Prueba manual desde la ruta /test")
    return f"Respuesta de Telegram: {res}"

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))

