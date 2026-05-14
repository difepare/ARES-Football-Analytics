# Instalar reportlab primero
# pip install reportlab

from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import inch
import io

def generar_pdf_informe(prediccion, filename="informe_ARES.pdf"):
    """Genera un informe PDF profesional"""
    
    doc = SimpleDocTemplate(filename, pagesize=letter)
    story = []
    styles = getSampleStyleSheet()
    
    # Título principal
    titulo = ParagraphStyle('Titulo', parent=styles['Title'], fontSize=24, textColor=colors.HexColor('#003366'))
    story.append(Paragraph("A.R.E.S. - Informe de Análisis Deportivo", titulo))
    story.append(Spacer(1, 20))
    
    # Datos del partido
    story.append(Paragraph(f"<b>Partido:</b> {prediccion['equipo_local']} vs {prediccion['equipo_visitante']}", styles['Normal']))
    story.append(Paragraph(f"<b>Fecha:</b> {prediccion['timestamp']}", styles['Normal']))
    story.append(Spacer(1, 20))
    
    # Tabla de probabilidades
    data = [
        ['Métrica', prediccion['equipo_local'], prediccion['equipo_visitante']],
        ['Probabilidad Victoria', f"{prediccion['prob_local']}%", f"{prediccion['prob_visitante']}%"],
        ['Goles Esperados (xG)', prediccion['xG_local'], prediccion['xG_visitante']],
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
    story.append(Spacer(1, 20))
    
    # Recomendación
    story.append(Paragraph("<b>Recomendación para Inversores:</b>", styles['Heading2']))
    story.append(Paragraph(prediccion['recomendacion'], styles['Normal']))
    
    doc.build(story)
    return filename