import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import requests
import json
import os
from enum import Enum
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import inch
import io
from dotenv import load_dotenv

# ============================================================
# CONFIGURACIÓN INICIAL
# ============================================================
load_dotenv()

st.set_page_config(
    page_title="A.R.E.S. - Sistema Avanzado de Evaluación",
    page_icon="⚽",
    layout="wide",
    initial_sidebar_state="expanded"
)

# API Configuration
API_KEY = os.getenv("API_FOOTBALL_KEY")
API_HOST = "v3.football.api-sports.io"

# Archivos de caché
CACHE_JUGADORES_FILE = "jugadores_cache.json"
CACHE_ACTUALIZACION_FILE = "ultima_actualizacion.txt"
HISTORIAL_FILE = "historial_predicciones.json"

# ============================================================
# CLASES BASE
# ============================================================
class Posicion(Enum):
    DELANTERO = "Delantero"
    MEDIOCAMPISTA = "Mediocampista"
    DEFENSA_CENTRAL = "Defensa Central"
    LATERAL = "Lateral"
    PORTERO = "Portero"

class NivelRiesgo(Enum):
    BAJO = "Bajo"
    MODERADO = "Moderado"
    ALTO = "Alto"
    CRITICO = "Critico"

class EstadisticasJugador:
    def __init__(self, nombre, posicion, edad, min7, min72, intensidad, distancia, lesiones, sprints, descanso):
        self.nombre = nombre
        self.posicion = posicion
        self.edad = edad
        self.minutos_jugados_7dias = min7
        self.minutos_jugados_72h = min72
        self.intensidad_media = intensidad
        self.distancia_recorrida = distancia
        self.historial_lesiones = lesiones
        self.sprints_por_partido = sprints
        self.dias_descanso_ultimo = descanso

# ============================================================
# LOGOS DE EQUIPOS
# ============================================================
LOGOS_EQUIPOS = {
    "Manchester City": "https://media.api-sports.io/football/teams/50.png",
    "Liverpool": "https://media.api-sports.io/football/teams/40.png",
    "Arsenal": "https://media.api-sports.io/football/teams/42.png",
    "Chelsea": "https://media.api-sports.io/football/teams/49.png",
    "Manchester United": "https://media.api-sports.io/football/teams/33.png",
    "Tottenham": "https://media.api-sports.io/football/teams/47.png",
    "Newcastle": "https://media.api-sports.io/football/teams/34.png",
    "Aston Villa": "https://media.api-sports.io/football/teams/66.png",
    "Real Madrid": "https://media.api-sports.io/football/teams/541.png",
    "Barcelona": "https://media.api-sports.io/football/teams/529.png",
    "Bayern Munich": "https://media.api-sports.io/football/teams/157.png",
    "Paris Saint-Germain": "https://media.api-sports.io/football/teams/85.png",
    "Inter Milan": "https://media.api-sports.io/football/teams/505.png",
    "AC Milan": "https://media.api-sports.io/football/teams/489.png",
}

def mostrar_logo_html(equipo):
    """Retorna HTML para mostrar el logo del equipo"""
    url_logo = LOGOS_EQUIPOS.get(equipo)
    if url_logo:
        return f'<img src="{url_logo}" width="50" style="border-radius: 50%; margin-right: 10px;">'
    return ""

# ============================================================
# FORMACIONES TÁCTICAS
# ============================================================
FORMACIONES = {
    "4-3-3": {
        "descripcion": "Ataque por bandas, presión alta",
        "recomendacion": "Ideal contra equipos que defienden en bloque bajo",
        "fortaleza": "Ataque",
        "debilidad": "Puede ser vulnerable al contragolpe"
    },
    "4-4-2": {
        "descripcion": "Equilibrio defensivo, doble pivote",
        "recomendacion": "Recomendado contra equipos con juego aéreo",
        "fortaleza": "Defensa",
        "debilidad": "Menos creatividad en el centro"
    },
    "4-5-1": {
        "descripcion": "Control del mediocampo, defensiva sólida",
        "recomendacion": "Para partidos donde se necesita proteger resultado",
        "fortaleza": "Control",
        "debilidad": "Ataque limitado"
    },
    "3-5-2": {
        "descripcion": "Ataque por carrileros, superioridad en medio",
        "recomendacion": "Ideal contra equipos con línea de 4",
        "fortaleza": "Mediocampo",
        "debilidad": "Defensa de 3 vulnerable"
    }
}

def recomendar_formacion(equipo_local, equipo_visitante):
    """Recomienda formación basada en la fuerza relativa"""
    # Lógica inteligente basada en equipos
    equipos_fuertes = ["Manchester City", "Liverpool", "Real Madrid", "Bayern Munich"]
    
    if equipo_local in equipos_fuertes:
        return "4-3-3"
    elif equipo_visitante in equipos_fuertes:
        return "4-5-1"
    else:
        return "4-4-2"

# ============================================================
# MÓDULO DE FATIGA
# ============================================================
class ModuloFatiga:
    def __init__(self):
        self.umbrales_minutos = {
            Posicion.DELANTERO: {"moderado": 270, "alto": 360, "critico": 450},
            Posicion.MEDIOCAMPISTA: {"moderado": 300, "alto": 390, "critico": 480},
            Posicion.DEFENSA_CENTRAL: {"moderado": 315, "alto": 405, "critico": 495},
            Posicion.LATERAL: {"moderado": 285, "alto": 375, "critico": 465},
            Posicion.PORTERO: {"moderado": 450, "alto": 540, "critico": 630},
        }
        
        self.factor_intensidad = {
            Posicion.DELANTERO: 1.3,
            Posicion.MEDIOCAMPISTA: 1.2,
            Posicion.DEFENSA_CENTRAL: 1.0,
            Posicion.LATERAL: 1.25,
            Posicion.PORTERO: 0.6,
        }
    
    def calcular_riesgo_fatiga(self, jugador, minuto_partido=0):
        umbrales = self.umbrales_minutos[jugador.posicion]
        
        minutos_factor = 0
        if jugador.minutos_jugados_7dias >= umbrales["critico"]:
            minutos_factor = 0.7
        elif jugador.minutos_jugados_7dias >= umbrales["alto"]:
            minutos_factor = 0.5
        elif jugador.minutos_jugados_7dias >= umbrales["moderado"]:
            minutos_factor = 0.3
        
        agudo_factor = min(0.5, jugador.minutos_jugados_72h / 180) if jugador.minutos_jugados_72h > 90 else 0
        intensidad_base = (jugador.intensidad_media / 100) * self.factor_intensidad[jugador.posicion]
        sprints_factor = (jugador.sprints_por_partido / 40) * 0.3
        lesiones_factor = min(0.4, jugador.historial_lesiones * 0.08)
        descanso_factor = max(0, 0.3 - (jugador.dias_descanso_ultimo * 0.05))
        minuto_factor = min(0.35, (minuto_partido / 90) * 0.35)
        
        probabilidad = min(0.95, (
            minutos_factor * 0.25 + agudo_factor * 0.20 + intensidad_base * 0.20 +
            sprints_factor * 0.10 + lesiones_factor * 0.15 + descanso_factor * 0.05 + minuto_factor * 0.05
        ))
        
        if probabilidad >= 0.65:
            nivel = NivelRiesgo.CRITICO
            sugerencia = "Sustitución inmediata - riesgo muy alto"
        elif probabilidad >= 0.45:
            nivel = NivelRiesgo.ALTO
            sugerencia = "Riesgo alto - preparar sustituto"
        elif probabilidad >= 0.25:
            nivel = NivelRiesgo.MODERADO
            sugerencia = "Fatiga moderada - reducir intensidad"
        else:
            nivel = NivelRiesgo.BAJO
            sugerencia = "Condición óptima"
        
        return {"nivel": nivel, "probabilidad": round(probabilidad * 100, 1), "sugerencia": sugerencia}

fatiga = ModuloFatiga()

# ============================================================
# SISTEMA DE TARJETAS
# ============================================================
class SistemaTarjetas:
    def __init__(self):
        self.factor_posicion = {
            Posicion.DELANTERO: 0.6,
            Posicion.MEDIOCAMPISTA: 1.0,
            Posicion.DEFENSA_CENTRAL: 1.2,
            Posicion.LATERAL: 1.1,
            Posicion.PORTERO: 0.2,
        }
        
        self.propension_base = {"Baja": 0.15, "Media": 0.35, "Alta": 0.55}
    
    def predecir_tarjeta_amarilla(self, jugador, minutos=90, intensidad=75, propension="Media"):
        prob_base = self.propension_base.get(propension, 0.35)
        prob_posicion = self.factor_posicion.get(jugador.posicion, 0.8)
        prob_intensidad = intensidad / 100
        prob_minutos = min(1.0, minutos / 90)
        
        riesgo_fatiga = jugador.minutos_jugados_7dias / 500 if jugador.minutos_jugados_7dias > 0 else 0
        prob_fatiga = min(0.4, riesgo_fatiga * 0.3)
        
        probabilidad = prob_base * prob_posicion * (0.7 + prob_intensidad * 0.3) * prob_minutos + prob_fatiga
        probabilidad = min(0.85, probabilidad)
        
        if probabilidad >= 0.5:
            nivel = "Alto 🔴"
            sugerencia = "Riesgo alto de tarjeta. Recomendar cuidado en entradas."
        elif probabilidad >= 0.3:
            nivel = "Medio 🟡"
            sugerencia = "Riesgo moderado. Evitar faltas tontas."
        else:
            nivel = "Bajo 🟢"
            sugerencia = "Riesgo bajo. Jugar con normalidad."
        
        return {"probabilidad": round(probabilidad * 100, 1), "nivel": nivel, "sugerencia": sugerencia}
    
    def predecir_tarjeta_roja(self, jugador, propension="Media", amarillas=0):
        prob_base = 0.08
        if amarillas >= 1:
            prob_base += 0.15
        if amarillas >= 2:
            prob_base += 0.25
        
        if propension == "Alta":
            prob_base *= 1.5
        elif propension == "Baja":
            prob_base *= 0.7
        
        prob_base *= self.factor_posicion.get(jugador.posicion, 0.8)
        probabilidad = min(0.35, prob_base)
        
        if probabilidad >= 0.2:
            nivel = "Alto 🔴"
            sugerencia = "Riesgo significativo de expulsión."
        elif probabilidad >= 0.1:
            nivel = "Medio 🟡"
            sugerencia = "Riesgo moderado de tarjeta roja."
        else:
            nivel = "Bajo 🟢"
            sugerencia = "Riesgo bajo de expulsión."
        
        return {"probabilidad": round(probabilidad * 100, 1), "nivel": nivel, "sugerencia": sugerencia}

sistema_tarjetas = SistemaTarjetas()

# ============================================================
# CONEXIÓN A API REAL
# ============================================================
def obtener_estadisticas_reales(equipo_nombre, league_id=39):
    """Obtiene estadísticas REALES desde API-Football"""
    
    if not API_KEY:
        return None
    
    headers = {"x-rapidapi-key": API_KEY, "x-rapidapi-host": API_HOST}
    
    # Buscar team_id
    url_team = f"https://{API_HOST}/teams"
    params = {"search": equipo_nombre}
    
    try:
        resp = requests.get(url_team, headers=headers, params=params, timeout=10)
        if resp.status_code == 200 and resp.json().get('response'):
            team_id = resp.json()['response'][0]['team']['id']
            
            # Obtener estadísticas
            url_stats = f"https://{API_HOST}/teams/statistics"
            params_stats = {"league": league_id, "season": 2025, "team": team_id}
            resp_stats = requests.get(url_stats, headers=headers, params=params_stats, timeout=10)
            
            if resp_stats.status_code == 200:
                stats = resp_stats.json()['response']
                
                form_str = stats.get('form', '')
                puntos_forma = form_str.count('W') * 3 + form_str.count('D')
                if puntos_forma >= 12:
                    forma = "Excelente 🔥"
                elif puntos_forma >= 9:
                    forma = "Buena 📈"
                elif puntos_forma >= 6:
                    forma = "Regular 📊"
                else:
                    forma = "Mala 📉"
                
                return {
                    "nombre": equipo_nombre,
                    "forma": forma,
                    "goles_favor": stats.get('goals', {}).get('for', {}).get('total', {}).get('average', 1.5),
                    "goles_contra": stats.get('goals', {}).get('against', {}).get('total', {}).get('average', 1.2),
                    "posesion": stats.get('possession', {}).get('average', 50),
                    "partidos": stats.get('fixtures', {}).get('played', {}).get('total', 0),
                    "victorias": stats.get('fixtures', {}).get('wins', {}).get('total', 0),
                }
    except Exception as e:
        print(f"Error API: {e}")
    
    return None

# ============================================================
# PREDICCIÓN DE PARTIDOS
# ============================================================
def predecir_partido(local, visitante):
    """Predicción con datos reales si están disponibles"""
    
    # Intentar obtener datos reales
    stats_local = obtener_estadisticas_reales(local)
    stats_visit = obtener_estadisticas_reales(visitante)
    
    if stats_local and stats_visit:
        # Usar datos reales
        fuerza_local = (stats_local['goles_favor'] * 10) + (stats_local['posesion'] / 10)
        fuerza_visit = (stats_visit['goles_favor'] * 10) + (stats_visit['posesion'] / 10)
        
        if "Excelente" in stats_local['forma']:
            fuerza_local *= 1.15
        if "Excelente" in stats_visit['forma']:
            fuerza_visit *= 1.15
        
        total = fuerza_local + fuerza_visit
        prob_local = (fuerza_local / total) * 0.7 + 0.15
        prob_visit = (fuerza_visit / total) * 0.7 + 0.15
        prob_empate = 1 - prob_local - prob_visit
        
        xG_local = round(stats_local['goles_favor'], 2)
        xG_visit = round(stats_visit['goles_favor'], 2)
        
        forma_local = stats_local['forma']
        forma_visit = stats_visit['forma']
        posesion_local = stats_local['posesion']
        posesion_visit = stats_visit['posesion']
        
        datos_reales = True
    else:
        # Datos simulados de respaldo
        equipos_data = {
            "Manchester City": {"fuerza": 92, "posesion": 62, "xG": 2.1, "forma": "Excelente 🔥"},
            "Liverpool": {"fuerza": 88, "posesion": 58, "xG": 1.9, "forma": "Buena 📈"},
            "Arsenal": {"fuerza": 84, "posesion": 55, "xG": 1.8, "forma": "Buena 📈"},
            "Chelsea": {"fuerza": 78, "posesion": 52, "xG": 1.6, "forma": "Regular 📊"},
            "Real Madrid": {"fuerza": 90, "posesion": 56, "xG": 2.0, "forma": "Excelente 🔥"},
            "Barcelona": {"fuerza": 85, "posesion": 64, "xG": 2.2, "forma": "Buena 📈"},
            "Bayern Munich": {"fuerza": 89, "posesion": 60, "xG": 2.1, "forma": "Excelente 🔥"},
        }
        
        data_local = equipos_data.get(local, {"fuerza": 80, "posesion": 50, "xG": 1.6, "forma": "Regular 📊"})
        data_visit = equipos_data.get(visitante, {"fuerza": 75, "posesion": 48, "xG": 1.4, "forma": "Regular 📊"})
        
        total = data_local["fuerza"] + data_visit["fuerza"]
        prob_local = (data_local["fuerza"] / total) * 0.7 + 0.15
        prob_visit = (data_visit["fuerza"] / total) * 0.7 + 0.15
        prob_empate = 1 - prob_local - prob_visit
        
        xG_local = data_local["xG"]
        xG_visit = data_visit["xG"]
        forma_local = data_local["forma"]
        forma_visit = data_visit["forma"]
        posesion_local = data_local["posesion"]
        posesion_visit = data_visit["posesion"]
        datos_reales = False
    
    # Confluencia de victoria
    factores = []
    if prob_local > 55:
        factores.append(f"✅ Mayor probabilidad de victoria local")
    if posesion_local > 55:
        factores.append(f"⚡ Alta posesión local ({posesion_local}%)")
    if "Excelente" in forma_local and "Mala" in forma_visit:
        factores.append(f"📈 Mejor momento de forma del local")
    
    return {
        'equipo_local': local, 'equipo_visitante': visitante,
        'xG_local': xG_local, 'xG_visitante': xG_visit,
        'prob_local': round(prob_local * 100, 1),
        'prob_empate': round(prob_empate * 100, 1),
        'prob_visitante': round(prob_visit * 100, 1),
        'forma_local': forma_local, 'forma_visitante': forma_visit,
        'posesion_local': posesion_local, 'posesion_visitante': posesion_visit,
        'confluencia': {
            'activada': len(factores) >= 2,
            'factores': factores,
            'sugerencia': '💡 Presionar desde el inicio' if len(factores) >= 2 else '🔍 Partido equilibrado'
        },
        'recomendacion': '🔥 Victoria local con alta confianza' if prob_local > 60 else '📈 Favorito local' if prob_local > 52 else '🤔 Partido equilibrado',
        'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        'datos_reales': datos_reales
    }

# ============================================================
# HISTORIAL Y PDF
# ============================================================
def guardar_prediccion(prediccion):
    historial = []
    if os.path.exists(HISTORIAL_FILE):
        with open(HISTORIAL_FILE, 'r', encoding='utf-8') as f:
            historial = json.load(f)
    
    historial.append({
        "id": len(historial) + 1,
        "fecha": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "local": prediccion['equipo_local'], "visitante": prediccion['equipo_visitante'],
        "prob_local": prediccion['prob_local'], "prob_empate": prediccion['prob_empate'],
        "prob_visitante": prediccion['prob_visitante'],
        "xG_local": prediccion['xG_local'], "xG_visitante": prediccion['xG_visitante'],
        "resultado_real": None, "acertado": None
    })
    
    with open(HISTORIAL_FILE, 'w', encoding='utf-8') as f:
        json.dump(historial, f, indent=2, ensure_ascii=False)

def cargar_historial():
    if os.path.exists(HISTORIAL_FILE):
        with open(HISTORIAL_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []

def generar_pdf_informe(prediccion):
    pdf_buffer = io.BytesIO()
    doc = SimpleDocTemplate(pdf_buffer, pagesize=letter)
    story = []
    styles = getSampleStyleSheet()
    
    titulo_style = ParagraphStyle('Titulo', parent=styles['Title'], fontSize=24, textColor=colors.HexColor('#003366'), alignment=1)
    story.append(Paragraph("A.R.E.S. - Informe de Análisis Deportivo", titulo_style))
    story.append(Spacer(1, 20))
    story.append(Paragraph(f"<b>Partido:</b> {prediccion['equipo_local']} vs {prediccion['equipo_visitante']}", styles['Normal']))
    story.append(Paragraph(f"<b>Fecha análisis:</b> {prediccion['timestamp']}", styles['Normal']))
    if prediccion.get('datos_reales'):
        story.append(Paragraph("<b>✅ Datos en tiempo real desde API-Football</b>", styles['Normal']))
    story.append(Spacer(1, 20))
    
    data = [
        ['Métrica', prediccion['equipo_local'], prediccion['equipo_visitante']],
        ['Probabilidad Victoria', f"{prediccion['prob_local']}%", f"{prediccion['prob_visitante']}%"],
        ['Goles Esperados (xG)', str(prediccion['xG_local']), str(prediccion['xG_visitante'])],
        ['Forma', prediccion['forma_local'], prediccion['forma_visitante']],
        ['Posesión Media', f"{prediccion['posesion_local']}%", f"{prediccion['posesion_visitante']}%"],
    ]
    
    table = Table(data, colWidths=[2*inch, 1.5*inch, 1.5*inch])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
    ]))
    story.append(table)
    story.append(Spacer(1, 20))
    story.append(Paragraph(f"<b>Recomendación:</b> {prediccion['recomendacion']}", styles['Normal']))
    
    doc.build(story)
    pdf_buffer.seek(0)
    return pdf_buffer

# ============================================================
# CATÁLOGO DE JUGADORES
# ============================================================
JUGADORES_BASE = {
    "Erling Haaland": {"posicion": "Delantero", "edad": 23, "equipo": "Manchester City", "intensidad_base": 88, "propension_tarjetas": "Baja", "lesiones_previas": 2},
    "Kevin De Bruyne": {"posicion": "Mediocampista", "edad": 32, "equipo": "Manchester City", "intensidad_base": 82, "propension_tarjetas": "Baja", "lesiones_previas": 3},
    "Phil Foden": {"posicion": "Mediocampista", "edad": 23, "equipo": "Manchester City", "intensidad_base": 84, "propension_tarjetas": "Baja", "lesiones_previas": 1},
    "Mohamed Salah": {"posicion": "Delantero", "edad": 31, "equipo": "Liverpool", "intensidad_base": 86, "propension_tarjetas": "Baja", "lesiones_previas": 1},
    "Virgil van Dijk": {"posicion": "Defensa Central", "edad": 32, "equipo": "Liverpool", "intensidad_base": 76, "propension_tarjetas": "Baja", "lesiones_previas": 2},
    "Bukayo Saka": {"posicion": "Delantero", "edad": 22, "equipo": "Arsenal", "intensidad_base": 86, "propension_tarjetas": "Baja", "lesiones_previas": 1},
    "Vinicius Jr": {"posicion": "Delantero", "edad": 23, "equipo": "Real Madrid", "intensidad_base": 88, "propension_tarjetas": "Media", "lesiones_previas": 2},
    "Jude Bellingham": {"posicion": "Mediocampista", "edad": 20, "equipo": "Real Madrid", "intensidad_base": 84, "propension_tarjetas": "Media", "lesiones_previas": 0},
    "Kylian Mbappe": {"posicion": "Delantero", "edad": 25, "equipo": "Real Madrid", "intensidad_base": 90, "propension_tarjetas": "Baja", "lesiones_previas": 1},
    "Robert Lewandowski": {"posicion": "Delantero", "edad": 35, "equipo": "Barcelona", "intensidad_base": 82, "propension_tarjetas": "Baja", "lesiones_previas": 1},
    "Harry Kane": {"posicion": "Delantero", "edad": 30, "equipo": "Bayern Munich", "intensidad_base": 84, "propension_tarjetas": "Baja", "lesiones_previas": 1},
    "Jamal Musiala": {"posicion": "Mediocampista", "edad": 21, "equipo": "Bayern Munich", "intensidad_base": 83, "propension_tarjetas": "Baja", "lesiones_previas": 1},
}

def inicializar_jugadores():
    """Inicializa el catálogo de jugadores"""
    if os.path.exists(CACHE_JUGADORES_FILE):
        with open(CACHE_JUGADORES_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return JUGADORES_BASE

# ============================================================
# ESTILOS CSS
# ============================================================
st.markdown("""
<style>
    .main-header { font-size: 2.5rem; font-weight: bold; text-align: center; background: linear-gradient(90deg, #00C9FF 0%, #92FE9D 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
    .risk-low { background-color: #e8f5e9; padding: 10px; border-radius: 10px; border-left: 4px solid #4caf50; margin: 5px 0; }
    .risk-moderate { background-color: #fff3e0; padding: 10px; border-radius: 10px; border-left: 4px solid #ff9800; margin: 5px 0; }
    .risk-high { background-color: #ffebee; padding: 10px; border-radius: 10px; border-left: 4px solid #f44336; margin: 5px 0; }
    .risk-critical { background-color: #ffcdd2; padding: 10px; border-radius: 10px; border-left: 4px solid #d32f2f; margin: 5px 0; }
    .formation-card { background-color: #1e1e2e; padding: 15px; border-radius: 10px; margin: 10px 0; }
    .real-data-badge { background-color: #4caf50; color: white; padding: 2px 8px; border-radius: 20px; font-size: 12px; display: inline-block; }
</style>
""", unsafe_allow_html=True)

# ============================================================
# INTERFAZ PRINCIPAL
# ============================================================
st.markdown('<div class="main-header">⚽ A.R.E.S. - El Cerebro del Fútbol ⚽</div>', unsafe_allow_html=True)
st.markdown('<p style="text-align: center">Advanced Real-time Evaluation System | Análisis Predictivo + Fatiga + Tarjetas + API Real</p>', unsafe_allow_html=True)
st.divider()

# Inicializar jugadores
JUGADORES = inicializar_jugadores()

# Sidebar
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/43/43101.png", width=80)
    st.title("🎮 Centro de Control")
    
    ligas = ["Premier League", "La Liga", "Champions League", "Serie A", "Bundesliga"]
    selected_league = st.selectbox("🏆 Liga / Competición", ligas)
    
    st.divider()
    
    col1, col2 = st.columns(2)
    with col1:
        local = st.text_input("🏠 Equipo Local", "Manchester City")
    with col2:
        visitante = st.text_input("✈️ Equipo Visitante", "Liverpool")
    
    st.divider()
    
    if st.button("🔄 Analizar Partido", use_container_width=True):
        st.rerun()
    
    st.divider()
    
    if API_KEY and API_KEY != "None":
        st.success("✅ API conectada")
    else:
        st.warning("⚠️ API no configurada")
    
    st.caption(f"📦 {len(JUGADORES)} jugadores en catálogo")

# Obtener predicción
prediccion = predecir_partido(local, visitante)
guardar_prediccion(prediccion)

# Badge de datos reales
if prediccion.get('datos_reales'):
    st.markdown('<span class="real-data-badge">✅ Datos en tiempo real desde API-Football</span>', unsafe_allow_html=True)
else:
    st.info("📊 Usando datos simulados de alta calidad (API no disponible o equipo no encontrado)")

# Tabs
tab1, tab2, tab3, tab4, tab5 = st.tabs(["📊 Análisis del Partido", "🩺 Fatiga + Tarjetas", "⚙️ Formaciones", "📜 Historial", "🏆 Champions"])

# ============================================================
# TAB 1: ANÁLISIS DEL PARTIDO
# ============================================================
with tab1:
    # Mostrar logos
    col_logo1, col_logo2, col_logo3 = st.columns([1, 1, 1])
    with col_logo1:
        st.markdown(mostrar_logo_html(local), unsafe_allow_html=True)
        st.markdown(f"### {local}")
    with col_logo2:
        st.markdown("### VS")
        st.markdown(f"### Empate: {prediccion['prob_empate']}%")
    with col_logo3:
        st.markdown(mostrar_logo_html(visitante), unsafe_allow_html=True)
        st.markdown(f"### {visitante}")
    
    st.divider()
    
    col_local, col_vs, col_visit = st.columns([2, 1, 2])
    
    with col_local:
        st.markdown(f"### 🏠 {local}")
        m1, m2 = st.columns(2)
        with m1:
            st.metric("🎯 Probabilidad Victoria", f"{prediccion['prob_local']}%", delta="Favorito" if prediccion['prob_local'] > 50 else "Underdog")
            st.metric("⚽ xG Esperado", prediccion['xG_local'])
        with m2:
            st.metric("📊 Forma", prediccion['forma_local'])
            st.metric("💪 Posesión", f"{prediccion['posesion_local']}%")
    
    with col_vs:
        fig = go.Figure(data=[go.Pie(
            labels=[local, "Empate", visitante],
            values=[prediccion['prob_local'], prediccion['prob_empate'], prediccion['prob_visitante']],
            hole=0.4,
            marker_colors=['#00C9FF', '#FFD700', '#FF6B6B']
        )])
        fig.update_layout(height=300, margin=dict(l=0, r=0, t=0, b=0))
        st.plotly_chart(fig, use_container_width=True)
    
    with col_visit:
        st.markdown(f"### ✈️ {visitante}")
        m1, m2 = st.columns(2)
        with m1:
            st.metric("🎯 Probabilidad Victoria", f"{prediccion['prob_visitante']}%")
            st.metric("⚽ xG Esperado", prediccion['xG_visitante'])
        with m2:
            st.metric("📊 Forma", prediccion['forma_visitante'])
            st.metric("💪 Posesión", f"{prediccion['posesion_visitante']}%")
    
    st.divider()
    st.subheader("⚡ SEÑALES DE ACCIÓN - CONFLUENCIA DE VICTORIA")
    
    if prediccion['confluencia']['activada']:
        st.success(f"✅ CONFLUENCIA ACTIVADA - {len(prediccion['confluencia']['factores'])} señales")
    else:
        st.info("⚠️ Confluencia no activada - Partido equilibrado")
    
    for factor in prediccion['confluencia']['factores']:
        st.success(factor)
    
    st.info(f"💡 {prediccion['confluencia']['sugerencia']}")
    
    st.divider()
    st.subheader("💰 RECOMENDACIÓN PARA INVERSORES")
    st.markdown(f"### {prediccion['recomendacion']}")
    
    if st.button("📄 Generar Informe PDF", use_container_width=True):
        pdf = generar_pdf_informe(prediccion)
        st.download_button("📥 Descargar PDF", pdf, file_name=f"ARES_{local}_vs_{visitante}.pdf", mime="application/pdf")

# ============================================================
# TAB 2: FATIGA + TARJETAS
# ============================================================
with tab2:
    st.subheader("🩺 Monitor de Fatiga y Riesgo Disciplinario")
    
    jugadores_lista = list(JUGADORES.keys())
    jugador_seleccionado = st.selectbox("🎽 Seleccionar Jugador", jugadores_lista, key="fatiga_select")
    
    if jugador_seleccionado:
        datos = JUGADORES[jugador_seleccionado]
        
        posicion_map = {
            "Delantero": Posicion.DELANTERO,
            "Mediocampista": Posicion.MEDIOCAMPISTA,
            "Defensa Central": Posicion.DEFENSA_CENTRAL,
            "Lateral": Posicion.LATERAL,
            "Portero": Posicion.PORTERO
        }
        posicion_enum = posicion_map.get(datos["posicion"], Posicion.DELANTERO)
        
        col_f1, col_f2 = st.columns(2)
        
        with col_f1:
            st.markdown("#### 📊 Carga de Partidos")
            minutos_7dias = st.slider("Minutos últimos 7 días", 0, 630, 300, key="min7")
            minutos_72h = st.slider("Minutos últimas 72h", 0, 270, 150, key="min72")
            intensidad = st.slider("Intensidad media", 0, 100, datos.get("intensidad_base", 80), key="int")
        
        with col_f2:
            st.markdown("#### 🏃‍♂️ Métricas")
            sprints = st.slider("Sprints por partido", 0, 50, 25, key="sprints")
            lesiones = st.number_input("Lesiones previas", 0, 10, datos.get("lesiones_previas", 1), key="lesiones")
            descanso = st.slider("Días desde último partido", 0, 14, 3, key="descanso")
        
        jugador = EstadisticasJugador(
            nombre=jugador_seleccionado,
            posicion=posicion_enum,
            edad=datos["edad"],
            min7=minutos_7dias,
            min72=minutos_72h,
            intensidad=intensidad,
            distancia=10.5,
            lesiones=lesiones,
            sprints=sprints,
            descanso=descanso
        )
        
        riesgo_fatiga = fatiga.calcular_riesgo_fatiga(jugador)
        
        st.divider()
        st.markdown("### 📊 Resultados")
        
        col_r1, col_r2, col_r3 = st.columns(3)
        
        with col_r1:
            st.markdown("#### 🩺 FATIGA")
            riesgo_color = "🟢" if riesgo_fatiga['probabilidad'] < 30 else "🟡" if riesgo_fatiga['probabilidad'] < 60 else "🔴"
            st.metric("Probabilidad Lesión", f"{riesgo_fatiga['probabilidad']}%", delta=riesgo_color)
            st.progress(riesgo_fatiga['probabilidad'] / 100)
            st.caption(riesgo_fatiga['sugerencia'])
        
        with col_r2:
            st.markdown("#### 🟨 TARJETA AMARILLA")
            riesgo_amarilla = sistema_tarjetas.predecir_tarjeta_amarilla(
                jugador, minutos_7dias, intensidad, datos.get("propension_tarjetas", "Media")
            )
            st.metric("Probabilidad", f"{riesgo_amarilla['probabilidad']}%")
            st.caption(riesgo_amarilla['sugerencia'])
        
        with col_r3:
            st.markdown("#### 🟥 TARJETA ROJA")
            riesgo_roja = sistema_tarjetas.predecir_tarjeta_roja(
                jugador, datos.get("propension_tarjetas", "Media")
            )
            st.metric("Probabilidad", f"{riesgo_roja['probabilidad']}%")
            st.caption(riesgo_roja['sugerencia'])
        
        if riesgo_fatiga['probabilidad'] > 65:
            st.error("🚨 **ALERTA CRÍTICA:** ¡Sustitución recomendada de inmediato!")

# ============================================================
# TAB 3: FORMACIONES
# ============================================================
with tab3:
    st.subheader("⚙️ Recomendación de Formación Táctica")
    
    formacion_recomendada = recomendar_formacion(local, visitante)
    formacion_data = FORMACIONES[formacion_recomendada]
    
    col_f1, col_f2 = st.columns(2)
    
    with col_f1:
        st.markdown(f"### Formación recomendada: {formacion_recomendada}")
        st.markdown(f"**{formacion_data['descripcion']}**")
        st.markdown(f"✅ **Fortaleza:** {formacion_data['fortaleza']}")
        st.markdown(f"⚠️ **Debilidad:** {formacion_data['debilidad']}")
        st.info(f"💡 **Recomendación táctica:** {formacion_data['recomendacion']}")
    
    with col_f2:
        st.markdown("### Otras formaciones disponibles")
        for formacion, info in FORMACIONES.items():
            if formacion != formacion_recomendada:
                with st.expander(f"📋 {formacion} - {info['fortaleza']}"):
                    st.write(info['descripcion'])
                    st.write(f"**Recomendado:** {info['recomendacion']}")

# ============================================================
# TAB 4: HISTORIAL
# ============================================================
with tab4:
    st.subheader("📜 Historial de Predicciones")
    
    historial = cargar_historial()
    
    if historial:
        st.metric("Total Predicciones", len(historial))
        
        df = pd.DataFrame(historial[::-1])
        columnas = ["fecha", "local", "visitante", "prob_local", "prob_visitante"]
        st.dataframe(df[columnas], use_container_width=True)
        
        if st.button("🗑️ Limpiar Historial", use_container_width=True):
            if os.path.exists(HISTORIAL_FILE):
                os.remove(HISTORIAL_FILE)
            st.success("Historial limpiado")
            st.rerun()
    else:
        st.info("No hay predicciones guardadas")

# ============================================================
# TAB 5: CHAMPIONS
# ============================================================
with tab5:
    st.subheader("🏆 Predicciones Champions League")
    
    favoritos = [
        ("Real Madrid", 92, "Excelente 🔥"),
        ("Manchester City", 89, "Excelente 🔥"),
        ("Bayern Munich", 87, "Buena 📈"),
        ("Barcelona", 84, "Buena 📈"),
        ("Liverpool", 82, "Buena 📈"),
        ("Paris SG", 80, "Regular 📊"),
    ]
    
    cols = st.columns(3)
    for i, (equipo, pts, forma) in enumerate(favoritos[:3]):
        with cols[i]:
            st.markdown(mostrar_logo_html(equipo), unsafe_allow_html=True)
            st.markdown(f"### {equipo}")
            st.metric("Puntuación", f"{pts} pts")
            st.caption(f"Forma: {forma}")
    
    st.divider()
    
    cuartos = [
        ("Real Madrid", "Bayern Munich", 52, 48),
        ("Manchester City", "Barcelona", 55, 45),
        ("Liverpool", "Paris Saint-Germain", 51, 49),
    ]
    
    for local_q, visit_q, prob_l, prob_v in cuartos:
        st.write(f"**{local_q}** {prob_l}% vs {prob_v}% **{visit_q}**")
        st.progress(prob_l / 100)

# ============================================================
# FOOTER
# ============================================================
st.divider()
st.caption(f"🕒 A.R.E.S. - Advanced Real-time Evaluation System | Actualizado: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | Datos: {'API Real' if prediccion.get('datos_reales') else 'Simulación de alta calidad'}")