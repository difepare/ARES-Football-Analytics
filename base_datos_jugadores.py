# ============================================================
# SISTEMA DE ACTUALIZACIÓN AUTOMÁTICA DE JUGADORES
# ============================================================

import requests
import json
import os
from datetime import datetime, timedelta

class ActualizadorJugadores:
    """
    Sincroniza los datos de los jugadores con la API de Football
    Se ejecuta automáticamente al iniciar o se puede forzar manualmente
    """
    
    def __init__(self, api_key, api_host):
        self.api_key = api_key
        self.api_host = api_host
        self.cache_file = "jugadores_cache.json"
        self.ultima_actualizacion_file = "ultima_actualizacion.txt"
    
    def _llamar_api(self, endpoint, params=None):
        """Realiza llamada a la API de Football"""
        url = f"https://{self.api_host}/{endpoint}"
        headers = {
            "x-rapidapi-key": self.api_key,
            "x-rapidapi-host": self.api_host
        }
        
        try:
            response = requests.get(url, headers=headers, params=params)
            if response.status_code == 200:
                return response.json()
            else:
                return None
        except Exception as e:
            print(f"Error en API: {e}")
            return None
    
    def buscar_jugador_en_api(self, nombre_jugador):
        """
        Busca un jugador en la API y devuelve su equipo actual
        """
        params = {"search": nombre_jugador}
        datos = self._llamar_api("players", params)
        
        if datos and datos.get('response'):
            for jugador in datos['response']:
                if jugador['player']['name'].lower() == nombre_jugador.lower():
                    return {
                        "equipo": jugador['statistics'][0]['team']['name'] if jugador.get('statistics') else "Desconocido",
                        "edad": jugador['player']['age'],
                        "nacionalidad": jugador['player']['nationality'],
                        "posicion": jugador['statistics'][0]['games']['position'] if jugador.get('statistics') else "Desconocida",
                        "actualizado": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    }
        return None
    
    def actualizar_jugador(self, nombre_jugador, datos_actuales):
        """
        Actualiza un jugador específico consultando la API
        """
        api_data = self.buscar_jugador_en_api(nombre_jugador)
        
        if api_data:
            # Actualizar el equipo
            datos_actuales["equipo"] = api_data["equipo"]
            datos_actuales["edad"] = api_data["edad"]
            datos_actuales["ultima_actualizacion"] = api_data["actualizado"]
            return True, api_data["equipo"]
        return False, None
    
    def actualizar_todos_los_jugadores(self, jugadores_dict):
        """
        Actualiza todos los jugadores del catálogo
        """
        actualizados = 0
        cambios = []
        
        for nombre, datos in jugadores_dict.items():
            # Consultar API (con límite para no exceder requests)
            api_data = self.buscar_jugador_en_api(nombre)
            
            if api_data:
                equipo_anterior = datos.get("equipo", "Desconocido")
                equipo_nuevo = api_data["equipo"]
                
                if equipo_anterior != equipo_nuevo and equipo_anterior != "Desconocido":
                    cambios.append({
                        "jugador": nombre,
                        "equipo_anterior": equipo_anterior,
                        "equipo_nuevo": equipo_nuevo
                    })
                
                # Actualizar datos
                datos["equipo"] = equipo_nuevo
                datos["edad"] = api_data["edad"]
                datos["ultima_actualizacion"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                actualizados += 1
        
        return actualizados, cambios
    
    def guardar_cache(self, jugadores_dict):
        """Guarda el catálogo actualizado en caché"""
        with open(self.cache_file, 'w', encoding='utf-8') as f:
            json.dump(jugadores_dict, f, indent=2, ensure_ascii=False)
        
        with open(self.ultima_actualizacion_file, 'w') as f:
            f.write(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    
    def cargar_cache(self):
        """Carga el catálogo desde caché"""
        if os.path.exists(self.cache_file):
            with open(self.cache_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return None
    
    def necesita_actualizacion(self, horas=24):
        """Verifica si pasaron más de X horas desde última actualización"""
        if os.path.exists(self.ultima_actualizacion_file):
            with open(self.ultima_actualizacion_file, 'r') as f:
                ultima_str = f.read().strip()
                try:
                    ultima = datetime.strptime(ultima_str, "%Y-%m-%d %H:%M:%S")
                    return datetime.now() - ultima > timedelta(hours=horas)
                except:
                    return True
        return True


# ============================================================
# INTEGRACIÓN EN EL DASHBOARD
# ============================================================

def inicializar_jugadores_con_api():
    """
    Inicializa el catálogo de jugadores, usando caché si es reciente
    o consultando API si es necesario
    """
    actualizador = ActualizadorJugadores(API_KEY, API_HOST)
    
    # Intentar cargar desde caché
    jugadores_cache = actualizador.cargar_cache()
    
    # Verificar si necesita actualización
    if jugadores_cache and not actualizador.necesita_actualizacion(horas=168):  # 7 días
        st.info(f"📦 Cargando {len(jugadores_cache)} jugadores desde caché (actualizado hace menos de 7 días)")
        return jugadores_cache
    
    # Si no hay caché o está desactualizado, mostrar opción
    if jugadores_cache:
        st.warning("⚠️ Los datos de jugadores tienen más de 7 días. ¿Deseas actualizar desde la API?")
        
        col_act1, col_act2 = st.columns(2)
        with col_act1:
            if st.button("🔄 Actualizar desde API"):
                with st.spinner("Actualizando jugadores... Esto puede tomar unos segundos"):
                    actualizados, cambios = actualizador.actualizar_todos_los_jugadores(jugadores_cache)
                    actualizador.guardar_cache(jugadores_cache)
                    
                    if cambios:
                        st.success(f"✅ {actualizados} jugadores actualizados")
                        for cambio in cambios:
                            st.info(f"📝 {cambio['jugador']}: {cambio['equipo_anterior']} → {cambio['equipo_nuevo']}")
                    else:
                        st.success(f"✅ {actualizados} jugadores verificados. Sin cambios.")
                    return jugadores_cache
        with col_act2:
            if st.button("📦 Usar caché (sin actualizar)"):
                return jugadores_cache
    else:
        # Primera vez: usar datos base
        st.info("📋 Catálogo inicial de jugadores cargado. Puedes actualizar manualmente cuando quieras.")
    
    return JUGADORES_DISPONIBLES  # Datos base