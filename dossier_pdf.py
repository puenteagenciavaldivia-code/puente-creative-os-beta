"""PDF editorial sin red ni activos externos; mismo dossier validado que HTML."""
from io import BytesIO
from xml.sax.saxutils import escape
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, ListFlowable, ListItem
from dossier_engine import validate_dossier, digest


def dossier_pdf(dossier):
    validation=validate_dossier(dossier)
    if validation['errors']:
        raise ValueError('El dossier contiene errores; no se puede exportar.')
    buffer=BytesIO()
    styles=getSampleStyleSheet()
    styles.add(ParagraphStyle(name='PuenteTitle',fontName='Times-Bold',fontSize=29,leading=33,textColor=colors.HexColor('#152639'),spaceAfter=18))
    styles.add(ParagraphStyle(name='PuenteHeading',fontName='Helvetica-Bold',fontSize=11,leading=14,textColor=colors.HexColor('#995234'),spaceBefore=10,spaceAfter=4))
    styles.add(ParagraphStyle(name='PuenteBody',fontName='Helvetica',fontSize=10.5,leading=14,spaceAfter=6,alignment=TA_LEFT))
    styles.add(ParagraphStyle(name='PuenteSmall',fontName='Helvetica',fontSize=8,leading=11,textColor=colors.HexColor('#57636f'),spaceAfter=8))
    story=[]
    def text(value,style='PuenteBody'):
        story.append(Paragraph(escape(str(value)),styles[style]))
    def section(label,value):
        text(label,'PuenteHeading');text(value)
    def bullets(values):
        for v in values:text('• '+str(v))
    def footer(canvas,doc):
        canvas.setStrokeColor(colors.HexColor('#bc7759'));canvas.line(20*mm,17*mm,190*mm,17*mm)
        canvas.setFont('Helvetica',8);canvas.setFillColor(colors.HexColor('#57636f'))
        canvas.drawString(20*mm,12*mm,'PUENTE | Dirección creativa | Borrador para revisión humana')
        canvas.drawRightString(190*mm,12*mm,str(doc.page))
    text('PUENTE / CREATIVE OS','PuenteSmall')
    text(dossier['brand'],'PuenteTitle')
    text('Propuesta de dirección creativa','PuenteHeading')
    text('Exploración profesional. La producción gráfica es una decisión posterior independiente.','PuenteSmall')
    section('El encargo',dossier['brief'])
    section('Público',dossier['audience'])
    section('Problema de comunicación',dossier['communication_problem'])
    section('Objetivo',dossier['objective'])
    text('Restricciones','PuenteHeading');bullets(dossier['constraints'])
    for direction in dossier['directions']:
        story.append(PageBreak())
        text('ALTERNATIVA '+direction['id'],'PuenteSmall');text(direction['name'],'PuenteTitle')
        section('Idea madre',direction['big_idea'])
        for key,label in [('insight','Observación de partida'),('promise','Promesa comunicacional'),('visual_system','Sistema visual'),('typography','Tipografía'),('photography','Dirección fotográfica'),('composition','Composición'),('differentiation','Diferenciación')]:
            section(label,direction[key])
        text('Aplicaciones indicativas','PuenteHeading')
        for key,value in direction['applications'].items():text(key.title()+': '+value)
        text('Riesgos y revisión pendiente','PuenteHeading');bullets(direction['risks'])
    story.append(PageBreak());text('Comparar antes de elegir','PuenteTitle')
    section('Criterios',', '.join(dossier['comparison']['criteria']))
    section('Balance editorial',dossier['comparison']['tradeoffs'])
    section('Recomendación para revisión',dossier['comparison']['recommendation'])
    for key,value in dossier['comparison']['rejected_reasons'].items():section('Alternativa '+key,value)
    text('Procedencia y límites','PuenteHeading')
    for source in dossier['source_register']:text(source['id']+' | '+source['origin']+' | '+source['usage'])
    for warning in validation['warnings']:text(warning,'PuenteSmall')
    text('No constituye aprobación del cliente, autorización de producción ni evidencia de eficacia publicitaria.','PuenteSmall')
    text('Integridad del dossier: '+digest(dossier),'PuenteSmall')
    SimpleDocTemplate(buffer,pagesize=A4,rightMargin=20*mm,leftMargin=20*mm,topMargin=20*mm,bottomMargin=24*mm,
                      title=dossier['brand']+' - Dirección creativa',author='Agencia Puente').build(story,onFirstPage=footer,onLaterPages=footer)
    return buffer.getvalue()
