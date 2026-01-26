import os
import requests
from flask import Flask, request, jsonify
from datetime import datetime
import firebase_admin
from firebase_admin import credentials, db

app = Flask(__name__)

# --- CONFIGURACIÓN FIREBASE (UNIFICADA) ---
nombre_archivo_credenciales = 'alpha50-fcc77-firebase-adminsdk-fbsvc-a9f291f3ef.json'
url_database = 'https://alpha50-fcc77-default-rtdb.europe-west1.firebasedatabase.app'

if not firebase_admin._apps:
    try:
        cred = credentials.Certificate(nombre_archivo_credenciales)
        firebase_admin.initialize_app(cred, {
            'databaseURL': url_database
        })
        print("✅ Conexión con Alpha50-Firebase establecida.")
    except Exception as e:
        print(f"❌ Error al conectar con Firebase: {e}")

# --- FUNCIONES DE TELEGRAM ---
TOKEN = os.environ.get("TELEGRAM_TOKEN")
CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

def enviar_a_telegram(mensaje):
    if not TOKEN or not CHAT_ID:
        return "Faltan variables de entorno"
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": mensaje}
    try:
        r = requests.post(url, json=payload, timeout=5)
        return r.text
    except Exception as e:
        return str(e)

# --- RUTAS ---
@app.route('/', methods=['GET', 'POST'])
def alpha50_webhook():
    enviar_a_telegram("✅ Sistema Alpha50 reiniciado y operativo.")
    return "OK"


@app.route('/test')
def test_bot():
    res = enviar_a_telegram("🎯 Prueba manual desde la ruta /test")
    return f"Respuesta de Telegram: {res}"

if __name__ == "__main__":
    # Importante: Cloud Run dicta el puerto por variable de entorno
    port = int(os.environ.get("PORT", 8080))
    app.run(debug=False, host="0.0.0.0", port=port)


