import json
from datetime import datetime
import os

HISTORIAL_FILE = "historial_predicciones.json"

def guardar_prediccion(prediccion):
    """Guarda la predicción en el historial"""
    
    historial = []
    if os.path.exists(HISTORIAL_FILE):
        with open(HISTORIAL_FILE, 'r', encoding='utf-8') as f:
            historial = json.load(f)
    
    registro = {
        "fecha": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "local": prediccion['equipo_local'],
        "visitante": prediccion['equipo_visitante'],
        "prob_local": prediccion['prob_local'],
        "xG_local": prediccion['xG_local'],
        "resultado_real": None  # Para actualizar después del partido
    }
    
    historial.append(registro)
    
    with open(HISTORIAL_FILE, 'w', encoding='utf-8') as f:
        json.dump(historial, f, indent=2, ensure_ascii=False)
    
    return len(historial)

def cargar_historial():
    """Carga el historial de predicciones"""
    if os.path.exists(HISTORIAL_FILE):
        with open(HISTORIAL_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []