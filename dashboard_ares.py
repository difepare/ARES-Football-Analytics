import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime
import sys

# Importar nuestros módulos (asumiendo que están en el mismo directorio)
# Por ahora recreamos las clases aquí para que funcione independiente

# [Aquí pegarías las clases ARES_Engine y ModuloFatigaAvanzada]
# Pero para que puedas probarlo YA, voy a poner versiones simplificadas

st.set_page_config(
    page_title="A.R.E.S. - Advanced Real-time Evaluation System",
    page_icon="⚽",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilo personalizado
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        background: linear-gradient(90deg, #00C9FF 0%, #92FE9D 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
    }
    .risk-low {
        background-color: #00ff8844;
        padding: 10px;
        border-radius: 10px;
        border-left: 4px solid #00ff88;
    }
    .risk-moderate {
        background-color: #ffaa0044;
        padding: 10px;
        border-radius: 10px;
        border-left: 4px solid #ffaa00;
    }
    .risk-high {
        background-color: #ff444444;
        padding: 10px;
        border-radius: 10px;
        border-left: 4px solid #ff4444;
    }
    .risk-critical {
        background-color: #aa000044;
        padding: 10px;
        border-radius: 10px;
        border-left: 4px solid #ff0000;
    }
</style>
""", unsafe_allow_html=True)

# Título
st.markdown('<div class="main-header">⚽ A.R.E.S. ⚽</div>', unsafe_allow_html=True)
st.markdown('<p style="text-align: center">Advanced Real-time Evaluation System - El Cerebro del Fútbol</p>', unsafe_allow_html=True)
st.divider()

# Sidebar
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/43/43101.png", width=80)
    st.title("🎮 Control Center")
    
    # Selector de partido
    partido = st.selectbox(
        "📋 Seleccionar Partido",
        ["Manchester City vs Liverpool", "Arsenal vs Chelsea", "Real Madrid vs Barcelona", "Bayern vs Dortmund"]
    )
    
    # Minuto del partido
    minuto = st.slider("⏱️ Minuto del Partido", 0, 90, 45, 5)
    
    st.divider()
    
    # Modo de visualización
    modo = st.radio(
        "👁️ Modo de Visualización",
        ["🎯 Tactical (B2B)", "📈 Oráculo (B2C)"],
        horizontal=True
    )
    
    st.divider()
    
    st.info("💡 **Consejo:** Activa la confluencia de victoria para ver señales de acción en tiempo real")

# Columnas principales
col1, col2 = st.columns(2)

with col1:
    st.subheader(f"🏠 {partido.split(' vs ')[0]}")
    
    # Métricas del equipo local
    metricas_local = st.columns(4)
    with metricas_local[0]:
        st.metric("🎯 Prob. Victoria", "58%", "+5%")
    with metricas_local[1]:
        st.metric("⚽ xG Esperado", "1.87", "+0.32")
    with metricas_local[2]:
        st.metric("💪 Posesión", "62%", "+3%")
    with metricas_local[3]:
        st.metric("⚠️ Fatiga", "32%", "+8%")
    
    # Mapa de calor (simulado)
    st.subheader("🗺️ Mapa de Calor - Ocupación")
    heat_data = np.random.rand(10, 10)
    fig = px.imshow(heat_data, 
                    labels=dict(x="Ancho del campo", y="Largo del campo", color="Intensidad"),
                    color_continuous_scale="RdYlGn_r")
    fig.update_layout(height=400, margin=dict(l=0, r=0, t=0, b=0))
    st.plotly_chart(fig, use_container_width=True)

with col2:
    st.subheader(f"✈️ {partido.split(' vs ')[1]}")
    
    # Métricas del equipo visitante
    metricas_visitante = st.columns(4)
    with metricas_visitante[0]:
        st.metric("🎯 Prob. Victoria", "27%", "-3%")
    with metricas_visitante[1]:
        st.metric("⚽ xG Esperado", "1.32", "-0.15")
    with metricas_visitante[2]:
        st.metric("💪 Posesión", "38%", "-2%")
    with metricas_visitante[3]:
        st.metric("⚠️ Fatiga", "45%", "+12%")
    
    # Gráfico de probabilidad de gol
    st.subheader("⏰ Probabilidad de Gol por Intervalo")
    tiempos = ['0-15', '16-30', '31-45', '46-60', '61-75', '76-90']
    prob_local = [0.12, 0.15, 0.18, 0.22, 0.25, 0.35]
    prob_visit = [0.10, 0.12, 0.14, 0.16, 0.18, 0.22]
    
    fig = go.Figure()
    fig.add_trace(go.Bar(x=tiempos, y=prob_local, name=partido.split(' vs ')[0], marker_color='#00C9FF'))
    fig.add_trace(go.Bar(x=tiempos, y=prob_visit, name=partido.split(' vs ')[1], marker_color='#FF6B6B'))
    fig.update_layout(barmode='group', height=350, margin=dict(l=0, r=0, t=20, b=0))
    st.plotly_chart(fig, use_container_width=True)

# Sección de Confluencia de Victoria
st.divider()
st.subheader("⚡ SEÑALES DE ACCIÓN - CONFLUENCIA DE VICTORIA")

col_signal1, col_signal2, col_signal3, col_signal4 = st.columns(4)

with col_signal1:
    st.success("✅ Baja posesión rival fuera de casa")
with col_signal2:
    st.warning("⚠️ Extremos locales +32% velocidad")
with col_signal3:
    st.error("😩 Fatiga crítica en defensa rival")
with col_signal4:
    st.success("⏰ Historial de goles tardíos (últimos 15')")

st.info("💡 **ACCIÓN RECOMENDADA:** Presionar salida por banda izquierda. Confluencia 3/4 factores activada.")

# Sección de Fatiga
st.divider()
st.subheader("🩺 MONITOR DE FATIGA - TIEMPO REAL")

fatiga_cols = st.columns(3)

with fatiga_cols[0]:
    with st.container():
        st.markdown('<div class="risk-moderate">', unsafe_allow_html=True)
        st.write("**🔵 Kevin De Bruyne** (Mediocampista)")
        st.progress(0.38, text="Fatiga: 38%")
        st.caption("🟡 Riesgo moderado - Monitorear")
        st.markdown('</div>', unsafe_allow_html=True)

with fatiga_cols[1]:
    with st.container():
        st.markdown('<div class="risk-high">', unsafe_allow_html=True)
        st.write("**🔴 Erling Haaland** (Delantero)")
        st.progress(0.58, text="Fatiga: 58%")
        st.caption("🔴 Riesgo alto - Preparar sustituto")
        st.markdown('</div>', unsafe_allow_html=True)

with fatiga_cols[2]:
    with st.container():
        st.markdown('<div class="risk-low">', unsafe_allow_html=True)
        st.write("**🟢 Ruben Dias** (Defensa)")
        st.progress(0.22, text="Fatiga: 22%")
        st.caption("🟢 Riesgo bajo - Continuar")
        st.markdown('</div>', unsafe_allow_html=True)

# Predicción de lesión
if minuto > 65:
    st.warning("🚨 **ALERTA CRÍTICA:** Si Haaland continúa a esta intensidad, la probabilidad de lesión sube al 72% en los próximos 10 minutos. **¡Sustitución recomendada!**")

# Footer
st.divider()
st.caption(f"🕒 Última actualización: {datetime.now().strftime('%H:%M:%S')} | A.R.E.S. v1.0 | El Cerebro del Fútbol")