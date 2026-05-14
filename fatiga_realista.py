# ============================================================
# TAB 3: MONITOR DE FATIGA MEJORADO (CON SELECTOR)
# ============================================================

with tab3:
    st.subheader("🩺 Monitor de Fatiga en Tiempo Real")
    
    # Pestañas dentro del monitor de fatiga
    fatiga_tab1, fatiga_tab2, fatiga_tab3 = st.tabs(["📋 Jugadores Predefinidos", "🔍 Buscar por Equipo", "✏️ Crear Jugador Personalizado"])
    
    # ========================================================
    # TAB 3.1: JUGADORES PREDEFINIDOS
    # ========================================================
    with fatiga_tab1:
        st.markdown("### Selecciona un jugador del catálogo")
        
        jugadores_lista = list(JUGADORES_DISPONIBLES.keys())
        jugador_seleccionado = st.selectbox("Jugador", jugadores_lista, key="fatiga_select")
        
        if jugador_seleccionado:
            datos = JUGADORES_DISPONIBLES[jugador_seleccionado]
            
            # Sliders para ajustar minutos jugados (simulando carga reciente)
            st.markdown("#### Carga de partidos recientes (simulación)")
            
            col_c1, col_c2 = st.columns(2)
            with col_c1:
                minutos_7dias = st.slider("Minutos últimos 7 días", 0, 630, 340, key=f"min7_{jugador_seleccionado}")
                minutos_72h = st.slider("Minutos últimas 72 horas", 0, 270, 180, key=f"min72_{jugador_seleccionado}")
                sprints = st.slider("Sprints por partido", 0, 50, 28, key=f"sprints_{jugador_seleccionado}")
            
            with col_c2:
                intensidad = st.slider("Intensidad media (0-100)", 0, 100, datos["intensidad_base"], key=f"int_{jugador_seleccionado}")
                distancia = st.slider("Distancia recorrida (km)", 0.0, 15.0, 10.5, key=f"dist_{jugador_seleccionado}")
                lesiones = st.slider("N° lesiones últimas 2 temporadas", 0, 5, 1, key=f"lesiones_{jugador_seleccionado}")
            
            dias_descanso = st.slider("Días desde último partido", 0, 14, 3, key=f"descanso_{jugador_seleccionado}")
            
            # Crear jugador con los parámetros ajustados
            jugador = EstadisticasJugador(
                nombre=jugador_seleccionado,
                posicion=datos["posicion"],
                edad=datos["edad"],
                min7=minutos_7dias,
                min72=minutos_72h,
                intensidad=intensidad,
                distancia=distancia,
                lesiones=lesiones,
                sprints=sprints,
                descanso=dias_descanso
            )
            
            # Calcular y mostrar riesgo
            riesgo = fatiga.calcular_riesgo_fatiga(jugador)
            
            st.divider()
            st.markdown("### 📊 Resultado del Análisis")
            
            col_r1, col_r2 = st.columns(2)
            with col_r1:
                if riesgo['nivel'] == NivelRiesgo.BAJO:
                    st.success(f"**Nivel de Riesgo:** {riesgo['nivel'].value}")
                elif riesgo['nivel'] == NivelRiesgo.MODERADO:
                    st.warning(f"**Nivel de Riesgo:** {riesgo['nivel'].value}")
                else:
                    st.error(f"**Nivel de Riesgo:** {riesgo['nivel'].value}")
                
                st.metric("Probabilidad de Lesión", f"{riesgo['probabilidad']}%")
            
            with col_r2:
                st.info(f"**Recomendación:** {riesgo['sugerencia']}")
                
                # Barra de progreso visual
                if riesgo['probabilidad'] < 30:
                    st.progress(riesgo['probabilidad'] / 100, text="🟢 Estado físico óptimo")
                elif riesgo['probabilidad'] < 60:
                    st.progress(riesgo['probabilidad'] / 100, text="🟡 Monitorear carga")
                else:
                    st.progress(riesgo['probabilidad'] / 100, text="🔴 Riesgo elevado")
            
            # Recomendación de sustitución
            if riesgo['probabilidad'] > 65:
                st.error("🚨 **ALERTA CRÍTICA:** ¡Sustitución recomendada de inmediato!")
            elif riesgo['probabilidad'] > 45:
                st.warning("⚠️ **ALERTA:** Preparar sustituto para los próximos 15-20 minutos")
    
    # ========================================================
    # TAB 3.2: BUSCAR POR EQUIPO
    # ========================================================
    with fatiga_tab2:
        st.markdown("### Buscar jugadores por equipo")
        
        # Obtener equipos únicos
        equipos = sorted(set(datos["equipo"] for datos in JUGADORES_DISPONIBLES.values()))
        equipo_seleccionado = st.selectbox("Seleccionar equipo", ["Todos"] + equipos, key="equipo_fatiga")
        
        if equipo_seleccionado == "Todos":
            jugadores_equipo = JUGADORES_DISPONIBLES
        else:
            jugadores_equipo = {n: d for n, d in JUGADORES_DISPONIBLES.items() if d.get("equipo") == equipo_seleccionado}
        
        st.markdown(f"**{len(jugadores_equipo)} jugadores encontrados**")
        
        for nombre, datos in jugadores_equipo.items():
            with st.expander(f"🎽 {nombre} - {datos['equipo']} ({datos['posicion'].value})"):
                # Sliders rápidos para este jugador
                minutos = st.slider("Minutos últimos 7 días", 0, 630, 300, key=f"min7_exp_{nombre}")
                intensidad_rapida = st.slider("Intensidad", 0, 100, datos["intensidad_base"], key=f"int_exp_{nombre}")
                
                jugador_temp = EstadisticasJugador(
                    nombre=nombre,
                    posicion=datos["posicion"],
                    edad=datos["edad"],
                    min7=minutos,
                    min72=150,
                    intensidad=intensidad_rapida,
                    distancia=10.0,
                    lesiones=1,
                    sprints=25,
                    descanso=3
                )
                
                riesgo_temp = fatiga.calcular_riesgo_fatiga(jugador_temp)
                
                if riesgo_temp['probabilidad'] < 30:
                    st.success(f"🟢 Riesgo: {riesgo_temp['probabilidad']}% - {riesgo_temp['sugerencia']}")
                elif riesgo_temp['probabilidad'] < 60:
                    st.warning(f"🟡 Riesgo: {riesgo_temp['probabilidad']}% - {riesgo_temp['sugerencia']}")
                else:
                    st.error(f"🔴 Riesgo: {riesgo_temp['probabilidad']}% - {riesgo_temp['sugerencia']}")
    
    # ========================================================
    # TAB 3.3: CREAR JUGADOR PERSONALIZADO
    # ========================================================
    with fatiga_tab3:
        st.markdown("### ✏️ Crear Jugador Personalizado")
        st.info("Ingresa los datos de cualquier jugador que quieras analizar")
        
        col_p1, col_p2 = st.columns(2)
        
        with col_p1:
            nombre_personalizado = st.text_input("Nombre del jugador", "Mi Jugador")
            
            posicion_personalizado = st.selectbox(
                "Posición",
                [Posicion.DELANTERO, Posicion.MEDIOCAMPISTA, Posicion.DEFENSA_CENTRAL, Posicion.LATERAL, Posicion.PORTERO],
                format_func=lambda x: x.value
            )
            
            edad_personalizado = st.number_input("Edad", 16, 45, 25)
            
            minutos_7dias_pers = st.number_input("Minutos últimos 7 días", 0, 630, 270)
            minutos_72h_pers = st.number_input("Minutos últimas 72 horas", 0, 270, 150)
        
        with col_p2:
            intensidad_pers = st.slider("Intensidad media (0-100)", 0, 100, 75)
            distancia_pers = st.slider("Distancia recorrida por partido (km)", 0.0, 15.0, 9.5)
            lesiones_pers = st.number_input("N° lesiones últimas 2 temporadas", 0, 10, 1)
            sprints_pers = st.number_input("Sprints por partido", 0, 50, 22)
            dias_descanso_pers = st.number_input("Días desde último partido", 0, 30, 4)
        
        if st.button("🔬 Analizar Jugador Personalizado", use_container_width=True):
            jugador_pers = EstadisticasJugador(
                nombre=nombre_personalizado,
                posicion=posicion_personalizado,
                edad=edad_personalizado,
                min7=minutos_7dias_pers,
                min72=minutos_72h_pers,
                intensidad=intensidad_pers,
                distancia=distancia_pers,
                lesiones=lesiones_pers,
                sprints=sprints_pers,
                descanso=dias_descanso_pers
            )
            
            riesgo_pers = fatiga.calcular_riesgo_fatiga(jugador_pers)
            
            st.divider()
            st.markdown(f"### Resultado para {nombre_personalizado}")
            
            col_r1, col_r2 = st.columns(2)
            with col_r1:
                if riesgo_pers['probabilidad'] < 30:
                    st.success(f"**Nivel de Riesgo:** 🟢 Bajo")
                elif riesgo_pers['probabilidad'] < 60:
                    st.warning(f"**Nivel de Riesgo:** 🟡 Moderado")
                else:
                    st.error(f"**Nivel de Riesgo:** 🔴 Alto")
                
                st.metric("Probabilidad de Lesión", f"{riesgo_pers['probabilidad']}%")
            
            with col_r2:
                st.info(f"**Recomendación:** {riesgo_pers['sugerencia']}")
                st.progress(riesgo_pers['probabilidad'] / 100)
            
            # Opción para guardar en el catálogo
            if st.button("💾 Guardar este jugador en el catálogo"):
                JUGADORES_DISPONIBLES[nombre_personalizado] = {
                    "posicion": posicion_personalizado,
                    "edad": edad_personalizado,
                    "equipo": "Personalizado",
                    "intensidad_base": intensidad_pers
                }
                st.success(f"✅ {nombre_personalizado} guardado en el catálogo")
                st.rerun()

    # ============================================================
# NUEVA SECCIÓN: RIESGO DISCIPLINARIO (TARJETAS)
# ============================================================

with tab3:
    # ... (código existente del monitor de fatiga) ...
    
    # Nueva sección de tarjetas
    st.divider()
    st.subheader("🟨🟥 Riesgo Disciplinario - Tarjetas Amarillas y Rojas")
    
    with st.expander("📋 Análisis de Tarjetas para Jugador Seleccionado", expanded=True):
        if jugador_seleccionado:
            datos_jugador = JUGADORES_DISPONIBLES[jugador_seleccionado]
            
            col_t1, col_t2, col_t3 = st.columns(3)
            
            with col_t1:
                st.markdown("#### 🟨 Tarjeta Amarilla")
                riesgo_amarilla = sistema_tarjetas.predecir_tarjeta_amarilla(
                    jugador, minutos_jugados=minutos_7dias, intensidad_partido=intensidad
                )
                st.metric("Probabilidad", f"{riesgo_amarilla['probabilidad']}%")
                st.caption(f"Nivel: {riesgo_amarilla['nivel']}")
                st.caption(f"💡 {riesgo_amarilla['sugerencia']}")
            
            with col_t2:
                st.markdown("#### 🟥 Tarjeta Roja")
                riesgo_roja = sistema_tarjetas.predecir_tarjeta_roja(jugador)
                st.metric("Probabilidad", f"{riesgo_roja['probabilidad']}%")
                st.caption(f"Nivel: {riesgo_roja['nivel']}")
                st.caption(f"💡 {riesgo_roja['sugerencia']}")
            
            with col_t3:
                st.markdown("#### ⚠️ Riesgo Total")
                riesgo_total = sistema_tarjetas.riesgo_disciplinario_total(jugador, minutos_7dias)
                
                if riesgo_total['puntaje'] >= 60:
                    st.error(f"**Puntaje: {riesgo_total['puntaje']}**")
                elif riesgo_total['puntaje'] >= 35:
                    st.warning(f"**Puntaje: {riesgo_total['puntaje']}**")
                else:
                    st.success(f"**Puntaje: {riesgo_total['puntaje']}**")
                
                st.caption(f"Nivel: {riesgo_total['nivel']}")
                st.info(riesgo_total['recomendacion'])
            
            # Factores que influyen
            with st.expander("📊 Factores que influyen en el riesgo disciplinario"):
                st.write(f"• **Propensión histórica:** {riesgo_amarilla['factores']['propension']}")
                st.write(f"• **Posición:** {riesgo_amarilla['factores']['posicion']} (factor {sistema_tarjetas.factor_posicion.get(jugador.posicion, 0.8)})")
                st.write(f"• **Intensidad del partido:** {riesgo_amarilla['factores']['intensidad']}%")
                st.write(f"• **Fatiga acumulada:** {riesgo_amarilla['factores']['fatiga']}%")
        else:
            st.info("Selecciona un jugador para ver el análisis de tarjetas")

        # En el sidebar o en TAB 3
with st.sidebar:
    st.divider()
    st.subheader("🔄 Sincronización de Datos")
    
    if st.button("🔄 Actualizar equipos de jugadores", use_container_width=True):
        with st.spinner("Consultando API para verificar cambios de equipo..."):
            actualizador = ActualizadorJugadores(API_KEY, API_HOST)
            
            # Buscar jugadores específicos que pueden haber cambiado
            jugadores_a_verificar = ["Kylian Mbappe", "Jude Bellingham", "Erling Haaland"]
            
            cambios_encontrados = []
            for nombre in jugadores_a_verificar:
                if nombre in JUGADORES_DISPONIBLES:
                    exito, nuevo_equipo = actualizador.actualizar_jugador(nombre, JUGADORES_DISPONIBLES[nombre])
                    if exito and nuevo_equipo != JUGADORES_DISPONIBLES[nombre]["equipo"]:
                        cambios_encontrados.append(f"{nombre}: → {nuevo_equipo}")
                        JUGADORES_DISPONIBLES[nombre]["equipo"] = nuevo_equipo
            
            if cambios_encontrados:
                st.success("✅ Cambios detectados y actualizados:")
                for cambio in cambios_encontrados:
                    st.info(cambio)
            else:
                st.info("📭 No se detectaron cambios de equipo")
            
            # Guardar en caché
            actualizador.guardar_cache(JUGADORES_DISPONIBLES)
            st.rerun()                