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
}

def mostrar_logo_html(equipo):
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
    },
    "4-4-2": {
        "descripcion": "Equilibrio defensivo, doble pivote",
        "recomendacion": "Recomendado contra equipos con juego aéreo",
        "fortaleza": "Defensa",
    },
    "4-5-1": {
        "descripcion": "Control del mediocampo, defensiva sólida",
        "recomendacion": "Para partidos donde se necesita proteger resultado",
        "fortaleza": "Control",
    },
    "3-5-2": {
        "descripcion": "Ataque por carrileros, superioridad en medio",
        "recomendacion": "Ideal contra equipos con línea de 4",
        "fortaleza": "Mediocampo",
    }
}

def recomendar_formacion(equipo_local, equipo_visitante):
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
            sugerencia = "Riesgo alto de tarjeta"
        elif probabilidad >= 0.3:
            nivel = "Medio 🟡"
            sugerencia = "Riesgo moderado"
        else:
            nivel = "Bajo 🟢"
            sugerencia = "Riesgo bajo"
        
        return {"probabilidad": round(probabilidad * 100, 1), "nivel": nivel, "sugerencia": sugerencia}
    
    def predecir_tarjeta_roja(self, jugador, propension="Media", amarillas=0):
        prob_base = 0.08
        if amarillas >= 1:
            prob_base += 0.15
        
        if propension == "Alta":
            prob_base *= 1.5
        elif propension == "Baja":
            prob_base *= 0.7
        
        prob_base *= self.factor_posicion.get(jugador.posicion, 0.8)
        probabilidad = min(0.35, prob_base)
        
        if probabilidad >= 0.2:
            nivel = "Alto 🔴"
            sugerencia = "Riesgo significativo de expulsión"
        elif probabilidad >= 0.1:
            nivel = "Medio 🟡"
            sugerencia = "Riesgo moderado"
        else:
            nivel = "Bajo 🟢"
            sugerencia = "Riesgo bajo"
        
        return {"probabilidad": round(probabilidad * 100, 1), "nivel": nivel, "sugerencia": sugerencia}

sistema_tarjetas = SistemaTarjetas()

# ============================================================
# PREDICCIÓN DE PARTIDOS
# ============================================================
def predecir_partido(local, visitante):
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
    
    factores = []
    if prob_local > 55:
        factores.append(f"✅ Mayor probabilidad de victoria local")
    if data_local["posesion"] > 55:
        factores.append(f"⚡ Alta posesión local ({data_local['posesion']}%)")
    
    return {
        'equipo_local': local, 'equipo_visitante': visitante,
        'xG_local': data_local["xG"], 'xG_visitante': data_visit["xG"],
        'prob_local': round(prob_local * 100, 1),
        'prob_empate': round(prob_empate * 100, 1),
        'prob_visitante': round(prob_visit * 100, 1),
        'forma_local': data_local["forma"], 'forma_visitante': data_visit["forma"],
        'posesion_local': data_local["posesion"], 'posesion_visitante': data_visit["posesion"],
        'confluencia': {
            'activada': len(factores) >= 2,
            'factores': factores,
            'sugerencia': '💡 Presionar desde el inicio' if len(factores) >= 2 else '🔍 Partido equilibrado'
        },
        'recomendacion': '🔥 Victoria local con alta confianza' if prob_local > 60 else '📈 Favorito local',
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
    story.append(Spacer(1, 20))
    
    data = [
        ['Métrica', prediccion['equipo_local'], prediccion['equipo_visitante']],
        ['Probabilidad Victoria', f"{prediccion['prob_local']}%", f"{prediccion['prob_visitante']}%"],
        ['Goles Esperados (xG)', str(prediccion['xG_local']), str(prediccion['xG_visitante'])],
        ['Forma', prediccion['forma_local'], prediccion['forma_visitante']],
    ]
    
    table = Table(data, colWidths=[2*inch, 1.5*inch, 1.5*inch])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
    ]))
    story.append(table)
    doc.build(story)
    pdf_buffer.seek(0)
    return pdf_buffer

# ============================================================
# CATÁLOGO DE JUGADORES
# ============================================================
JUGADORES_BASE = {
    "Erling Haaland": {"posicion": "Delantero", "edad": 23, "equipo": "Manchester City", "intensidad_base": 88, "propension_tarjetas": "Baja", "lesiones_previas": 2},
    "Kevin De Bruyne": {"posicion": "Mediocampista", "edad": 32, "equipo": "Manchester City", "intensidad_base": 82, "propension_tarjetas": "Baja", "lesiones_previas": 3},
    "Mohamed Salah": {"posicion": "Delantero", "edad": 31, "equipo": "Liverpool", "intensidad_base": 86, "propension_tarjetas": "Baja", "lesiones_previas": 1},
    "Vinicius Jr": {"posicion": "Delantero", "edad": 23, "equipo": "Real Madrid", "intensidad_base": 88, "propension_tarjetas": "Media", "lesiones_previas": 2},
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
    .main-header { font-size: 2rem; font-weight: bold; text-align: center; color: #00C9FF; }
    .risk-low { background-color: #e8f5e9; padding: 10px; border-radius: 10px; border-left: 4px solid #4caf50; margin: 5px 0; }
    .risk-moderate { background-color: #fff3e0; padding: 10px; border-radius: 10px; border-left: 4px solid #ff9800; margin: 5px 0; }
    .risk-high { background-color: #ffebee; padding: 10px; border-radius: 10px; border-left: 4px solid #f44336; margin: 5px 0; }
    .risk-critical { background-color: #ffcdd2; padding: 10px; border-radius: 10px; border-left: 4px solid #d32f2f; margin: 5px 0; }
</style>
""", unsafe_allow_html=True)

# ============================================================
# INTERFAZ PRINCIPAL
# ============================================================
st.markdown('<div class="main-header">⚽ A.R.E.S. - El Cerebro del Fútbol ⚽</div>', unsafe_allow_html=True)
st.markdown('<p style="text-align: center">Advanced Real-time Evaluation System</p>', unsafe_allow_html=True)
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
    st.caption(f"📦 {len(JUGADORES)} jugadores en catálogo")

# Obtener predicción
prediccion = predecir_partido(local, visitante)
guardar_prediccion(prediccion)

# ============================================================
# TABS
# ============================================================
tab1, tab2, tab3, tab4 = st.tabs(["📊 Análisis del Partido", "🩺 Fatiga + Tarjetas", "⚙️ Formaciones", "📜 Historial"])

# ============================================================
# TAB 1: ANÁLISIS DEL PARTIDO
# ============================================================
with tab1:
    col_local, col_vs, col_visit = st.columns([2, 1, 2])
    
    with col_local:
        st.markdown(f"### 🏠 {local}")
        m1, m2 = st.columns(2)
        with m1:
            st.metric("🎯 Probabilidad Victoria", f"{prediccion['prob_local']}%")
            st.metric("⚽ xG Esperado", prediccion['xG_local'])
        with m2:
            st.metric("📊 Forma", prediccion['forma_local'])
            st.metric("💪 Posesión", f"{prediccion['posesion_local']}%")
    
    with col_vs:
        st.markdown("### 🤝 VS")
        st.markdown(f"### Empate: {prediccion['prob_empate']}%")
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
    st.subheader("⚡ SEÑALES DE ACCIÓN")
    for factor in prediccion['confluencia']['factores']:
        st.success(factor)
    st.info(f"💡 {prediccion['confluencia']['sugerencia']}")
    
    if st.button("📄 Generar PDF", use_container_width=True):
        pdf = generar_pdf_informe(prediccion)
        st.download_button("📥 Descargar PDF", pdf, file_name=f"ARES_{local}_vs_{visitante}.pdf", mime="application/pdf")

# ============================================================
# TAB 2: FATIGA + TARJETAS
# ============================================================
with tab2:
    st.subheader("🩺 Monitor de Fatiga")
    
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
        
        minutos_7dias = st.slider("Minutos últimos 7 días", 0, 630, 300)
        minutos_72h = st.slider("Minutos últimas 72h", 0, 270, 150)
        intensidad = st.slider("Intensidad media", 0, 100, datos.get("intensidad_base", 80))
        
        jugador = EstadisticasJugador(
            nombre=jugador_seleccionado, posicion=posicion_enum, edad=datos["edad"],
            min7=minutos_7dias, min72=minutos_72h, intensidad=intensidad,
            distancia=10.5, lesiones=datos.get("lesiones_previas", 1), sprints=25, descanso=3
        )
        
        riesgo_fatiga = fatiga.calcular_riesgo_fatiga(jugador)
        riesgo_amarilla = sistema_tarjetas.predecir_tarjeta_amarilla(jugador, minutos_7dias, intensidad, datos.get("propension_tarjetas", "Media"))
        
        col_r1, col_r2 = st.columns(2)
        with col_r1:
            st.metric("Probabilidad Lesión", f"{riesgo_fatiga['probabilidad']}%")
            st.progress(riesgo_fatiga['probabilidad'] / 100)
            st.caption(riesgo_fatiga['sugerencia'])
        with col_r2:
            st.metric("Probabilidad Tarjeta Amarilla", f"{riesgo_amarilla['probabilidad']}%")
            st.caption(riesgo_amarilla['sugerencia'])

# ============================================================
# TAB 3: FORMACIONES
# ============================================================
with tab3:
    st.subheader("⚙️ Recomendación de Formación")
    
    formacion_recomendada = recomendar_formacion(local, visitante)
    formacion_data = FORMACIONES[formacion_recomendada]
    
    st.markdown(f"### Formación recomendada: {formacion_recomendada}")
    st.markdown(f"**{formacion_data['descripcion']}**")
    st.info(f"💡 {formacion_data['recomendacion']}")

# ============================================================
# TAB 4: HISTORIAL
# ============================================================
with tab4:
    st.subheader("📜 Historial de Predicciones")
    historial = cargar_historial()
    if historial:
        df = pd.DataFrame(historial[::-1])
        st.dataframe(df[["fecha", "local", "visitante", "prob_local", "prob_visitante"]], use_container_width=True)
    else:
        st.info("No hay predicciones guardadas")

# ============================================================
# FOOTER
# ============================================================
st.divider()
st.caption(f"🕒 A.R.E.S. - Actualizado: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")