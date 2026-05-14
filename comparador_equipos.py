# Agrega esta función al dashboard

def comparador_equipos(equipo1, equipo2):
    """Comparación head-to-head detallada"""
    
    # Datos simulados de enfrentamientos históricos
    enfrentamientos = {
        ("Manchester City", "Liverpool"): {
            "total": 52, "victorias_local": 18, "empates": 12, "victorias_visitante": 22,
            "goles_local": 78, "goles_visitante": 85,
            "ultimo_encuentro": "Manchester City 1-1 Liverpool",
            "racha_local": "3 partidos sin perder",
            "racha_visitante": "2 partidos sin ganar"
        },
        ("Real Madrid", "Barcelona"): {
            "total": 256, "victorias_local": 78, "empates": 62, "victorias_visitante": 116,
            "goles_local": 312, "goles_visitante": 398,
            "ultimo_encuentro": "Real Madrid 3-2 Barcelona",
            "racha_local": "2 victorias consecutivas",
            "racha_visitante": "1 derrota"
        }
    }
    
    key = (equipo1, equipo2)
    key_reverse = (equipo2, equipo1)
    
    if key in enfrentamientos:
        data = enfrentamientos[key]
        return {
            "local": equipo1,
            "visitante": equipo2,
            "total": data["total"],
            "victorias_local": data["victorias_local"],
            "empates": data["empates"],
            "victorias_visitante": data["victorias_visitante"],
            "goles_local": data["goles_local"],
            "goles_visitante": data["goles_visitante"],
            "ultimo": data["ultimo_encuentro"],
            "racha_local": data["racha_local"],
            "racha_visitante": data["racha_visitante"]
        }
    return None