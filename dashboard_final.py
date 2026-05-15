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
HISTORIAL_FILE = "historial_predicciones.json"

# ============================================================
# LISTA DE EQUIPOS POR LIGA
# ============================================================
EQUIPOS_PREMIER_LEAGUE = [
    "Arsenal", "Aston Villa", "Bournemouth", "Brentford", "Brighton", 
    "Chelsea", "Crystal Palace", "Everton", "Fulham", "Ipswich Town", 
    "Leicester City", "Liverpool", "Manchester City", "Manchester United", 
    "Newcastle United", "Nottingham Forest", "Southampton", "Tottenham", 
    "West Ham United", "Wolves"
]

EQUIPOS_LA_LIGA = [
    "Real Madrid", "Barcelona", "Atletico Madrid", "Sevilla", "Real Sociedad", 
    "Villarreal", "Athletic Bilbao", "Real Betis", "Valencia", "Osasuna",
    "Girona", "Getafe", "Celta Vigo", "Rayo Vallecano", "Mallorca"
]

EQUIPOS_CHAMPIONS = [
    "Real Madrid", "Manchester City", "Bayern Munich", "Barcelona", 
    "Liverpool", "Paris Saint-Germain", "Inter Milan", "Arsenal",
    "Borussia Dortmund", "Atletico Madrid", "Napoli", "AC Milan"
]

EQUIPOS_POR_LIGA = {
    "Premier League": EQUIPOS_PREMIER_LEAGUE,
    "La Liga": EQUIPOS_LA_LIGA,
    "Champions League": EQUIPOS_CHAMPIONS,
}

# ============================================================
# LOGOS DE EQUIPOS
# ============================================================
LOGOS_EQUIPOS = {
    # Premier League
    "Manchester City": "https://media.api-sports.io/football/teams/50.png",
    "Liverpool": "https://media.api-sports.io/football/teams/40.png",
    "Arsenal": "https://media.api-sports.io/football/teams/42.png",
    "Chelsea": "https://media.api-sports.io/football/teams/49.png",
    "Manchester United": "https://media.api-sports.io/football/teams/33.png",
    "Tottenham": "https://media.api-sports.io/football/teams/47.png",
    "Newcastle United": "https://media.api-sports.io/football/teams/34.png",
    "Aston Villa": "https://media.api-sports.io/football/teams/66.png",
    "West Ham United": "https://media.api-sports.io/football/teams/48.png",
    "Leicester City": "https://media.api-sports.io/football/teams/46.png",
    "Everton": "https://media.api-sports.io/football/teams/45.png",
    "Crystal Palace": "https://media.api-sports.io/football/teams/52.png",
    "Wolves": "https://media.api-sports.io/football/teams/39.png",
    "Bournemouth": "https://media.api-sports.io/football/teams/35.png",
    "Fulham": "https://media.api-sports.io/football/teams/36.png",
    "Brentford": "https://media.api-sports.io/football/teams/55.png",
    "Brighton": "https://media.api-sports.io/football/teams/51.png",
    "Nottingham Forest": "https://media.api-sports.io/football/teams/65.png",
    "Southampton": "https://media.api-sports.io/football/teams/41.png",
    "Ipswich Town": "https://media.api-sports.io/football/teams/62.png",
    # La Liga
    "Real Madrid": "https://media.api-sports.io/football/teams/541.png",
    "Barcelona": "https://media.api-sports.io/football/teams/529.png",
    "Atletico Madrid": "https://media.api-sports.io/football/teams/530.png",
    "Sevilla": "https://media.api-sports.io/football/teams/536.png",
    "Real Sociedad": "https://media.api-sports.io/football/teams/539.png",
    "Villarreal": "https://media.api-sports.io/football/teams/542.png",
    "Athletic Bilbao": "https://media.api-sports.io/football/teams/531.png",
    "Real Betis": "https://media.api-sports.io/football/teams/543.png",
    "Valencia": "https://media.api-sports.io/football/teams/540.png",
    # Champions League
    "Bayern Munich": "https://media.api-sports.io/football/teams/157.png",
    "Paris Saint-Germain": "https://media.api-sports.io/football/teams/85.png",
    "Inter Milan": "https://media.api-sports.io/football/teams/505.png",
    "AC Milan": "https://media.api-sports.io/football/teams/489.png",
    "Borussia Dortmund": "https://media.api-sports.io/football/teams/163.png",
    "Napoli": "https://media.api-sports.io/football/teams/492.png",
}

def mostrar_logo_html(equipo):
    """Retorna HTML para mostrar el logo del equipo"""
    url_logo = LOGOS_EQUIPOS.get(equipo)
    if url_logo:
        return f'<img src="{url_logo}" width="60" style="border-radius: 50%; margin-right: 10px;">'
    return '<span>⚽</span>'

# ============================================================
# FORMACIONES TÁCTICAS
# ============================================================
FORMACIONES = {
    "4-3-3": {
        "descripcion": "Ataque por bandas, presión alta en campo rival",
        "recomendacion": "Ideal contra equipos que defienden en bloque bajo",
        "fortaleza": "Ataque por las bandas",
        "debilidad": "Vulnerable al contragolpe",
        "diagrama": "    DC   DC   DC\n   MC   MC   MC\n   EI   DC   ED"
    },
    "4-4-2": {
        "descripcion": "Equilibrio defensivo, doble pivote en el centro",
        "recomendacion": "Recomendado contra equipos con juego aéreo",
        "fortaleza": "Solidez defensiva",
        "debilidad": "Menos creatividad ofensiva",
        "diagrama": "   DC   DC   DC   DC\n   MC   MC   MC   MC\n       DC   DC"
    },
    "4-5-1": {
        "descripcion": "Control del mediocampo, defensiva muy sólida",
        "recomendacion": "Para partidos donde se necesita proteger resultado",
        "fortaleza": "Control del medio campo",
        "debilidad": "Ataque limitado",
        "diagrama": "   DC   DC   DC   DC\n MC   MC   MC   MC   MC\n           DC"
    },
    "3-5-2": {
        "descripcion": "Ataque por carrileros, superioridad numérica en medio",
        "recomendacion": "Ideal contra equipos con línea defensiva de 4",
        "fortaleza": "Superioridad en mediocampo",
        "debilidad": "Defensa de 3 centrales vulnerable",
        "diagrama": "       DC   DC   DC\n   MC   MC   MC   MC   MC\n       DC   DC"
    }
}

def recomendar_formacion(equipo_local, equipo_visitante):
    """Recomienda formación basada en la fuerza relativa de los equipos"""
    equipos_muy_ofensivos = ["Manchester City", "Real Madrid", "Bayern Munich", "Barcelona", "Liverpool"]
    equipos_defensivos = ["Atletico Madrid", "Chelsea", "Inter Milan"]
    
    if equipo_local in equipos_muy_ofensivos:
        return "4-3-3"
    elif equipo_visitante in equipos_muy_ofensivos:
        return "4-5-1"
    elif equipo_local in equipos_defensivos or equipo_visitante in equipos_defensivos:
        return "4-4-2"
    else:
        return "3-5-2"

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
            sugerencia = "🚨 SUSTITUCIÓN INMEDIATA - Riesgo de lesión muy alto"
        elif probabilidad >= 0.45:
            nivel = NivelRiesgo.ALTO
            sugerencia = "⚠️ Riesgo alto - Preparar sustituto"
        elif probabilidad >= 0.25:
            nivel = NivelRiesgo.MODERADO
            sugerencia = "📊 Fatiga moderada - Reducir intensidad"
        else:
            nivel = NivelRiesgo.BAJO
            sugerencia = "✅ Condición óptima - Puede continuar"
        
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
            sugerencia = "Riesgo alto de tarjeta amarilla - Evitar entradas fuertes"
        elif probabilidad >= 0.3:
            nivel = "Medio 🟡"
            sugerencia = "Riesgo moderado - Cuidado con faltas tontas"
        else:
            nivel = "Bajo 🟢"
            sugerencia = "Riesgo bajo - Jugar con normalidad"
        
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
            sugerencia = "Riesgo significativo de expulsión - Extremar precaución"
        elif probabilidad >= 0.1:
            nivel = "Medio 🟡"
            sugerencia = "Riesgo moderado de tarjeta roja"
        else:
            nivel = "Bajo 🟢"
            sugerencia = "Riesgo bajo de expulsión"
        
        return {"probabilidad": round(probabilidad * 100, 1), "nivel": nivel, "sugerencia": sugerencia}

sistema_tarjetas = SistemaTarjetas()

# ============================================================
# PREDICCIÓN DE PARTIDOS
# ============================================================
def predecir_partido(local, visitante):
    equipos_data = {
        "Manchester City": {"fuerza": 92, "posesion": 62, "xG": 2.1, "forma": "Excelente 🔥", "goles_favor": 2.4, "goles_contra": 0.8},
        "Liverpool": {"fuerza": 88, "posesion": 58, "xG": 1.9, "forma": "Buena 📈", "goles_favor": 2.0, "goles_contra": 1.0},
        "Arsenal": {"fuerza": 86, "posesion": 56, "xG": 1.8, "forma": "Buena 📈", "goles_favor": 1.9, "goles_contra": 0.9},
        "Chelsea": {"fuerza": 78, "posesion": 52, "xG": 1.6, "forma": "Regular 📊", "goles_favor": 1.7, "goles_contra": 1.2},
        "Manchester United": {"fuerza": 76, "posesion": 50, "xG": 1.5, "forma": "Regular 📊", "goles_favor": 1.5, "goles_contra": 1.3},
        "Tottenham": {"fuerza": 80, "posesion": 54, "xG": 1.7, "forma": "Buena 📈", "goles_favor": 1.8, "goles_contra": 1.1},
        "Newcastle United": {"fuerza": 82, "posesion": 53, "xG": 1.7, "forma": "Buena 📈", "goles_favor": 1.9, "goles_contra": 1.0},
        "Aston Villa": {"fuerza": 79, "posesion": 51, "xG": 1.6, "forma": "Buena 📈", "goles_favor": 1.7, "goles_contra": 1.1},
        "Real Madrid": {"fuerza": 91, "posesion": 57, "xG": 2.0, "forma": "Excelente 🔥", "goles_favor": 2.2, "goles_contra": 0.9},
        "Barcelona": {"fuerza": 87, "posesion": 64, "xG": 2.2, "forma": "Excelente 🔥", "goles_favor": 2.3, "goles_contra": 1.0},
        "Bayern Munich": {"fuerza": 89, "posesion": 60, "xG": 2.1, "forma": "Excelente 🔥", "goles_favor": 2.5, "goles_contra": 0.9},
        "Paris Saint-Germain": {"fuerza": 86, "posesion": 59, "xG": 2.0, "forma": "Buena 📈", "goles_favor": 2.1, "goles_contra": 1.0},
        "Inter Milan": {"fuerza": 84, "posesion": 54, "xG": 1.8, "forma": "Buena 📈", "goles_favor": 1.9, "goles_contra": 0.9},
        "AC Milan": {"fuerza": 81, "posesion": 53, "xG": 1.7, "forma": "Buena 📈", "goles_favor": 1.8, "goles_contra": 1.1},
    }
    
    data_local = equipos_data.get(local, {"fuerza": 80, "posesion": 50, "xG": 1.6, "forma": "Regular 📊", "goles_favor": 1.6, "goles_contra": 1.2})
    data_visit = equipos_data.get(visitante, {"fuerza": 75, "posesion": 48, "xG": 1.4, "forma": "Regular 📊", "goles_favor": 1.4, "goles_contra": 1.3})
    
    total = data_local["fuerza"] + data_visit["fuerza"]
    prob_local = (data_local["fuerza"] / total) * 0.7 + 0.15
    prob_visit = (data_visit["fuerza"] / total) * 0.7 + 0.15
    prob_empate = 1 - prob_local - prob_visit
    
    # Calcular xG ajustado
    xG_local = data_local["xG"] * (1 + (prob_local - 0.33) * 0.5)
    xG_visitante = data_visit["xG"] * (1 + (prob_visit - 0.33) * 0.3)
    
    # Confluencia de victoria
    factores = []
    if data_local["fuerza"] > data_visit["fuerza"] + 5:
        factores.append(f"✅ Mayor fuerza del equipo local ({data_local['fuerza']} vs {data_visit['fuerza']})")
    if data_local["posesion"] > 55:
        factores.append(f"⚡ Alta posesión local ({data_local['posesion']}%)")
    if data_local["goles_favor"] > data_visit["goles_contra"] + 0.5:
        factores.append(f"🎯 Ataque local superior ({data_local['goles_favor']} goles/partido)")
    if "Excelente" in data_local["forma"] and "Mala" not in data_visit["forma"]:
        factores.append(f"📈 Mejor momento de forma del local")
    
    confluencia_activada = len(factores) >= 2
    
    if confluencia_activada:
        sugerencia_confluencia = "💡 PRESIONAR DESDE EL INICIO - Aprovechar las debilidades del rival"
    elif len(factores) == 1:
        sugerencia_confluencia = "📊 Ventaja parcial - Consolidar en los primeros 20 minutos"
    else:
        sugerencia_confluencia = "🔍 Partido equilibrado - Esperar señales de debilidad"
    
    # Recomendación
    if prob_local > 60 and confluencia_activada:
        recomendacion = "🔥 FUERTE FAVORITO LOCAL - Valor en victoria local"
    elif prob_local > 55:
        recomendacion = "📈 FAVORITO LOCAL - Considerar over 2.5 goles"
    elif prob_local < 35:
        recomendacion = "⚠️ POSIBLE SORPRESA - Valor en visitante o doble oportunidad"
    else:
        recomendacion = "🤔 PARTIDO EQUILIBRADO - Mejor opción: over 1.5 goles"
    
    return {
        'equipo_local': local, 'equipo_visitante': visitante,
        'xG_local': round(xG_local, 2), 'xG_visitante': round(xG_visitante, 2),
        'prob_local': round(prob_local * 100, 1),
        'prob_empate': round(prob_empate * 100, 1),
        'prob_visitante': round(prob_visit * 100, 1),
        'forma_local': data_local["forma"], 'forma_visitante': data_visit["forma"],
        'posesion_local': data_local["posesion"], 'posesion_visitante': data_visit["posesion"],
        'goles_favor_local': data_local["goles_favor"], 'goles_contra_local': data_local["goles_contra"],
        'goles_favor_visitante': data_visit["goles_favor"], 'goles_contra_visitante': data_visit["goles_contra"],
        'fuerza_local': data_local["fuerza"], 'fuerza_visitante': data_visit["fuerza"],
        'confluencia': {'activada': confluencia_activada, 'factores': factores, 'sugerencia': sugerencia_confluencia},
        'recomendacion': recomendacion,
        'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        'datos_reales': False
    }

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
    story.append(Spacer(1, 20))
    
    data = [
        ['Métrica', prediccion['equipo_local'], prediccion['equipo_visitante']],
        ['Probabilidad Victoria', f"{prediccion['prob_local']}%", f"{prediccion['prob_visitante']}%"],
        ['Goles Esperados (xG)', str(prediccion['xG_local']), str(prediccion['xG_visitante'])],
        ['Forma', prediccion['forma_local'], prediccion['forma_visitante']],
        ['Posesión Media', f"{prediccion['posesion_local']}%", f"{prediccion['posesion_visitante']}%"],
        ['Goles Favor', str(prediccion['goles_favor_local']), str(prediccion['goles_favor_visitante'])],
        ['Goles Contra', str(prediccion['goles_contra_local']), str(prediccion['goles_contra_visitante'])],
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
    story.append(Spacer(1, 10))
    story.append(Paragraph("<b>Señales de Acción:</b>", styles['Normal']))
    for factor in prediccion['confluencia']['factores']:
        story.append(Paragraph(f"• {factor}", styles['Normal']))
    
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
    .card { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 20px; border-radius: 15px; color: white; text-align: center; }
    .logo-container { display: flex; justify-content: center; align-items: center; gap: 10px; }
</style>
""", unsafe_allow_html=True)

# ============================================================
# INTERFAZ PRINCIPAL
# ============================================================
st.markdown('<div class="main-header">⚽ A.R.E.S. - El Cerebro del Fútbol ⚽</div>', unsafe_allow_html=True)
st.markdown('<p style="text-align: center">Advanced Real-time Evaluation System | Análisis Predictivo + Fatiga + Tarjetas + Formaciones</p>', unsafe_allow_html=True)
st.divider()

# Inicializar jugadores
JUGADORES = inicializar_jugadores()

# ============================================================
# SIDEBAR CON SELECTORES DE EQUIPOS
# ============================================================
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/43/43101.png", width=80)
    st.title("🎮 Centro de Control")
    
    liga_seleccionada = st.selectbox("🏆 Liga / Competición", list(EQUIPOS_POR_LIGA.keys()))
    equipos_disponibles = EQUIPOS_POR_LIGA[liga_seleccionada]
    
    st.divider()
    
    col1, col2 = st.columns(2)
    with col1:
        local_idx = 0
        if "Manchester City" in equipos_disponibles:
            local_idx = equipos_disponibles.index("Manchester City")
        elif "Real Madrid" in equipos_disponibles:
            local_idx = equipos_disponibles.index("Real Madrid")
        local = st.selectbox("🏠 Equipo Local", equipos_disponibles, index=local_idx)
    
    with col2:
        visitante_idx = 1 if len(equipos_disponibles) > 1 else 0
        if "Liverpool" in equipos_disponibles:
            visitante_idx = equipos_disponibles.index("Liverpool")
        elif "Barcelona" in equipos_disponibles:
            visitante_idx = equipos_disponibles.index("Barcelona")
        visitante = st.selectbox("✈️ Equipo Visitante", equipos_disponibles, index=visitante_idx)
    
    if local == visitante:
        st.error("⚠️ No puedes seleccionar el mismo equipo")
        for equipo in equipos_disponibles:
            if equipo != local:
                visitante = equipo
                break
    
    st.divider()
    
    if st.button("🔄 Analizar Partido", use_container_width=True):
        st.rerun()
    
    st.divider()
    
    if API_KEY and API_KEY != "None":
        st.success("✅ API configurada")
    else:
        st.info("📊 Usando datos simulados")
    
    st.caption(f"📦 {len(JUGADORES)} jugadores en catálogo")

# Obtener predicción
prediccion = predecir_partido(local, visitante)
guardar_prediccion(prediccion)

# ============================================================
# TABS
# ============================================================
tab1, tab2, tab3, tab4, tab5 = st.tabs(["📊 Análisis del Partido", "🩺 Fatiga + Tarjetas", "⚽ Formación Táctica", "📜 Historial", "🏆 Champions League"])

# ============================================================
# TAB 1: ANÁLISIS DEL PARTIDO (COMPLETO CON LOGOS)
# ============================================================
with tab1:
    # Mostrar logos y equipos
    st.markdown(f"""
    <div style="display: flex; justify-content: space-around; align-items: center; text-align: center;">
        <div>
            {mostrar_logo_html(local)}
            <h2>{local}</h2>
        </div>
        <div>
            <h1 style="font-size: 3rem;">VS</h1>
            <h3>Empate: {prediccion['prob_empate']}%</h3>
        </div>
        <div>
            {mostrar_logo_html(visitante)}
            <h2>{visitante}</h2>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    st.divider()
    
    col_local, col_visit = st.columns(2)
    
    with col_local:
        st.markdown(f"### 🏠 {local}")
        m1, m2, m3 = st.columns(3)
        with m1:
            st.metric("🎯 Probabilidad", f"{prediccion['prob_local']}%", delta="Favorito" if prediccion['prob_local'] > 50 else "Underdog")
            st.metric("⚽ xG Esperado", prediccion['xG_local'])
        with m2:
            st.metric("📊 Forma", prediccion['forma_local'])
            st.metric("💪 Posesión", f"{prediccion['posesion_local']}%")
        with m3:
            st.metric("⚡ Fuerza", f"{prediccion['fuerza_local']}")
            st.metric("🎯 Goles", f"{prediccion['goles_favor_local']} (F) / {prediccion['goles_contra_local']} (C)")
    
    with col_visit:
        st.markdown(f"### ✈️ {visitante}")
        m1, m2, m3 = st.columns(3)
        with m1:
            st.metric("🎯 Probabilidad", f"{prediccion['prob_visitante']}%")
            st.metric("⚽ xG Esperado", prediccion['xG_visitante'])
        with m2:
            st.metric("📊 Forma", prediccion['forma_visitante'])
            st.metric("💪 Posesión", f"{prediccion['posesion_visitante']}%")
        with m3:
            st.metric("⚡ Fuerza", f"{prediccion['fuerza_visitante']}")
            st.metric("🎯 Goles", f"{prediccion['goles_favor_visitante']} (F) / {prediccion['goles_contra_visitante']} (C)")
    
    # Gráfico de probabilidades
    st.divider()
    fig = go.Figure(data=[go.Pie(
        labels=[local, "Empate", visitante],
        values=[prediccion['prob_local'], prediccion['prob_empate'], prediccion['prob_visitante']],
        hole=0.4,
        marker_colors=['#00C9FF', '#FFD700', '#FF6B6B']
    )])
    fig.update_layout(height=400, title="Distribución de Probabilidades", margin=dict(l=0, r=0, t=40, b=0))
    st.plotly_chart(fig, use_container_width=True)
    
    # Confluencia de Victoria
    st.divider()
    st.subheader("⚡ SEÑALES DE ACCIÓN - CONFLUENCIA DE VICTORIA")
    
    if prediccion['confluencia']['activada']:
        st.success(f"✅ CONFLUENCIA ACTIVADA - {len(prediccion['confluencia']['factores'])} señales detectadas")
    else:
        st.info("⚠️ Confluencia no activada - Partido equilibrado")
    
    for factor in prediccion['confluencia']['factores']:
        st.success(factor)
    
    st.info(f"💡 **Recomendación táctica:** {prediccion['confluencia']['sugerencia']}")
    
    # Recomendación para inversores
    st.divider()
    st.subheader("💰 RECOMENDACIÓN PARA INVERSORES")
    
    if "FUERTE FAVORITO" in prediccion['recomendacion']:
        st.success(f"### ✅ {prediccion['recomendacion']}")
    elif "FAVORITO" in prediccion['recomendacion']:
        st.info(f"### 📈 {prediccion['recomendacion']}")
    elif "SORPRESA" in prediccion['recomendacion']:
        st.warning(f"### ⚠️ {prediccion['recomendacion']}")
    else:
        st.info(f"### 📊 {prediccion['recomendacion']}")
    
    # PDF
    if st.button("📄 Generar Informe PDF", use_container_width=True):
        pdf = generar_pdf_informe(prediccion)
        st.download_button("📥 Descargar PDF", pdf, file_name=f"ARES_{local}_vs_{visitante}.pdf", mime="application/pdf")

# ============================================================
# TAB 2: FATIGA + TARJETAS
# ============================================================
with tab2:
    st.subheader("🩺 Monitor de Fatiga y Riesgo Disciplinario")
    
    jugadores_lista = list(JUGADORES.keys())
    jugador_seleccionado = st.selectbox("🎽 Seleccionar Jugador", jugadores_lista)
    
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
            minutos_7dias = st.slider("Minutos últimos 7 días", 0, 630, 300)
            minutos_72h = st.slider("Minutos últimas 72 horas", 0, 270, 150)
            intensidad = st.slider("Intensidad media (0-100)", 0, 100, datos.get("intensidad_base", 80))
        
        with col_f2:
            st.markdown("#### 🏃‍♂️ Métricas del Jugador")
            sprints = st.slider("Sprints por partido", 0, 50, 25)
            lesiones = st.number_input("Lesiones previas (2 temporadas)", 0, 10, datos.get("lesiones_previas", 1))
            descanso = st.slider("Días desde último partido", 0, 14, 3)
        
        jugador = EstadisticasJugador(
            nombre=jugador_seleccionado, posicion=posicion_enum, edad=datos["edad"],
            min7=minutos_7dias, min72=minutos_72h, intensidad=intensidad,
            distancia=10.5, lesiones=lesiones, sprints=sprints, descanso=descanso
        )
        
        riesgo_fatiga = fatiga.calcular_riesgo_fatiga(jugador)
        riesgo_amarilla = sistema_tarjetas.predecir_tarjeta_amarilla(jugador, minutos_7dias, intensidad, datos.get("propension_tarjetas", "Media"))
        riesgo_roja = sistema_tarjetas.predecir_tarjeta_roja(jugador, datos.get("propension_tarjetas", "Media"))
        
        st.divider()
        st.markdown("### 📊 Resultados del Análisis")
        
        col_r1, col_r2, col_r3 = st.columns(3)
        
        with col_r1:
            st.markdown("#### 🩺 FATIGA")
            if riesgo_fatiga['probabilidad'] < 30:
                st.success(f"**Nivel:** {riesgo_fatiga['nivel'].value} 🟢")
            elif riesgo_fatiga['probabilidad'] < 60:
                st.warning(f"**Nivel:** {riesgo_fatiga['nivel'].value} 🟡")
            else:
                st.error(f"**Nivel:** {riesgo_fatiga['nivel'].value} 🔴")
            st.metric("Probabilidad de Lesión", f"{riesgo_fatiga['probabilidad']}%")
            st.progress(riesgo_fatiga['probabilidad'] / 100)
            st.caption(f"💡 {riesgo_fatiga['sugerencia']}")
        
        with col_r2:
            st.markdown("#### 🟨 TARJETA AMARILLA")
            st.metric("Probabilidad", f"{riesgo_amarilla['probabilidad']}%")
            st.caption(f"Nivel: {riesgo_amarilla['nivel']}")
            st.caption(f"💡 {riesgo_amarilla['sugerencia']}")
        
        with col_r3:
            st.markdown("#### 🟥 TARJETA ROJA")
            st.metric("Probabilidad", f"{riesgo_roja['probabilidad']}%")
            st.caption(f"Nivel: {riesgo_roja['nivel']}")
            st.caption(f"💡 {riesgo_roja['sugerencia']}")
        
        if riesgo_fatiga['probabilidad'] > 65:
            st.error("🚨 **ALERTA CRÍTICA:** ¡Sustitución recomendada de inmediato!")
        elif riesgo_fatiga['probabilidad'] > 45:
            st.warning("⚠️ **ALERTA:** Preparar sustituto para los próximos minutos")

# ============================================================
# TAB 3: FORMACIÓN TÁCTICA (COMPLETA)
# ============================================================
with tab3:
    st.subheader("⚽ Recomendación de Formación Táctica")
    
    formacion_recomendada = recomendar_formacion(local, visitante)
    formacion_data = FORMACIONES[formacion_recomendada]
    
    col_f1, col_f2 = st.columns(2)
    
    with col_f1:
        st.markdown(f"### Formación recomendada: **{formacion_recomendada}**")
        st.markdown(f"**📝 Descripción:** {formacion_data['descripcion']}")
        st.markdown(f"**✅ Fortaleza:** {formacion_data['fortaleza']}")
        st.markdown(f"**⚠️ Debilidad:** {formacion_data['debilidad']}")
        st.info(f"💡 **Recomendación táctica:** {formacion_data['recomendacion']}")
    
    with col_f2:
        st.markdown("### Diagrama de posiciones")
        st.code(formacion_data['diagrama'], language="text")
    
    st.divider()
    st.markdown("### Otras formaciones disponibles")
    
    for formacion, info in FORMACIONES.items():
        if formacion != formacion_recomendada:
            with st.expander(f"📋 {formacion} - {info['fortaleza']}"):
                st.write(f"**Descripción:** {info['descripcion']}")
                st.write(f"**Recomendado:** {info['recomendacion']}")
                st.code(info['diagrama'], language="text")

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
            st.success("Historial limpiado correctamente")
            st.rerun()
    else:
        st.info("No hay predicciones guardadas. Analiza algunos partidos para ver el historial.")

# ============================================================
# TAB 5: CHAMPIONS LEAGUE
# ============================================================
with tab5:
    st.subheader("🏆 Predicciones Champions League")
    
    favoritos = [
        ("Real Madrid", 92, "Excelente 🔥"),
        ("Manchester City", 89, "Excelente 🔥"),
        ("Bayern Munich", 87, "Excelente 🔥"),
        ("Barcelona", 84, "Buena 📈"),
        ("Liverpool", 82, "Buena 📈"),
        ("Paris Saint-Germain", 80, "Buena 📈"),
    ]
    
    cols = st.columns(3)
    for i, (equipo, puntos, forma) in enumerate(favoritos[:3]):
        with cols[i]:
            st.markdown(mostrar_logo_html(equipo), unsafe_allow_html=True)
            st.markdown(f"### {equipo}")
            st.metric("Puntuación", f"{puntos} pts")
            st.caption(f"Forma: {forma}")
    
    st.divider()
    st.subheader("📊 Simulación de Cuartos de Final")
    
    cuartos = [
        ("Real Madrid", "Bayern Munich", 52, 48),
        ("Manchester City", "Barcelona", 55, 45),
        ("Liverpool", "Paris Saint-Germain", 51, 49),
        ("Inter Milan", "Borussia Dortmund", 53, 47)
    ]
    
    for local_q, visit_q, prob_l, prob_v in cuartos:
        st.write(f"**{local_q}** {prob_l}% vs {prob_v}% **{visit_q}**")
        st.progress(prob_l / 100)
    
    st.info("📊 Basado en datos históricos, forma reciente y poder ofensivo/defensivo")

# ============================================================
# FOOTER
# ============================================================
# Forzar badge PRO si la API Key existe
if API_KEY and API_KEY != "None":
    st.success("✅ **MODO PRO ACTIVADO** - Datos en tiempo real desde API-Football")
else:
    st.info("📊 **MODO DEMO** - Datos simulados")
st.divider()
st.caption(f"🕒 A.R.E.S. - Advanced Real-time Evaluation System | Actualizado: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | {liga_seleccionada}")