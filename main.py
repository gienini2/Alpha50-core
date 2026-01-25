import json
import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore

# Aquí es donde conectaríamos la llave del Paso 1
# Por ahora, este script inicializará la base de datos
def inicializar_sistema():
    if not firebase_admin._apps:
        # En el entorno de Google Cloud, esto se autentica solo
        cred = credentials.ApplicationDefault() 
        firebase_admin.initialize_app(cred)
    
    db = firestore.client()
    return db

def guardar_progreso(peso, agilidad, navette):
    db = inicializar_sistema()
    data = {
        'fecha': firestore.SERVER_TIMESTAMP,
        'peso': peso,
        'marcas': {
            'agilidad': agilidad,
            'navette': navette
        }
    }
    db.collection('progreso_agent1009').add(data)
    print("Datos persistidos en Firebase")

# Ejecución de prueba con tus datos de hoy
if __name__ == "__main__":
    guardar_progreso(92.4, 19.6, 8.0)
def calcular_puntos_gub(peso_actual, agilidad_seg, navette_palier):
    # Lógica basada en los baremos que me pasaste (>31 años)
    puntos_agilidad = 0
    if agilidad_seg <= 18.3: puntos_agilidad = 10
    elif agilidad_seg <= 19.5: puntos_agilidad = 4
    elif agilidad_seg <= 20.1: puntos_agilidad = 2
    
    return f"Estado Agent 1009: Puntos Agilidad = {puntos_agilidad}"

# Cargar tu JSON
with open('config.json') as f:
    data = json.load(f)

print(calcular_puntos_gub(data['historico_peso'][-1]['valor'], 
                         data['marcas_actuales']['agilidad_seg'], 
                         data['marcas_actuales']['course_navette_palier']))