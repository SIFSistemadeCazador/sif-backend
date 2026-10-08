from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware # <--- NUEVO
from pydantic import BaseModel
from sqlalchemy.orm import Session
import math
import datetime

import models
from database import engine, SessionLocal

models.Base.metadata.create_all(bind=engine)

app = FastAPI()

# --- NUEVO: PERMISO PARA QUE TU INTERFAZ WEB SE CONECTE ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Permite que cualquier HTML se conecte
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
        
class CazadorNuevo(BaseModel):
    nombre: str
    genero: str  # 'M' para que le hable de Leónidas o 'F' para Atenea

@app.post("/crear_cazador")
def crear_cazador(datos: CazadorNuevo, db: Session = Depends(get_db)):
    from fastapi import HTTPException
    
    # --- 1. CANDADO ANTI-CLONES ---
    # Buscamos en la base de datos si ya existe ese nombre de Cazador
    cazador_existente = db.query(models.Usuario).filter(models.Usuario.nombre == datos.nombre).first()
    
    if cazador_existente:
        # Si ya existe, abortamos la misión y lanzamos error
        raise HTTPException(status_code=400, detail="Ese Alias ya está ocupado por otro Cazador.")
        
    # --- 2. SI NO EXISTE, LO CREAMOS NORMALMENTE ---
    nuevo_usuario = models.Usuario(
        nombre=datos.nombre,
        genero=datos.genero
    )
    db.add(nuevo_usuario)
    db.commit()
    db.refresh(nuevo_usuario) # Recargamos para que la BD nos dé el número de ID oficial
    
    return {"tu_id_oficial": nuevo_usuario.id}

# 1. Agregamos el grupo_muscular al molde
class Entrenamiento(BaseModel):
    usuario_id: int
    peso_corporal_kg: float  # ¡Nuevo! Crucial para las categorías y multiplicadores
    ejercicio: str
    grupo_muscular: str
    peso: float
    unidad: str
    repeticiones: int
    series: int

# --- EL CATÁLOGO MAESTRO DE REPARTO DE XP (100 EJERCICIOS) ---
CATALOGO_EJERCICIOS = {
    # --- PECHO (15) ---
    "Press de Banca Plano": {"Pecho": 0.70, "Tríceps": 0.20, "Hombro Frontal": 0.10},
    "Press Inclinado con Barra": {"Pecho Superior": 0.60, "Hombro Frontal": 0.30, "Tríceps": 0.10},
    "Press Declinado con Barra": {"Pecho Inferior": 0.70, "Tríceps": 0.20, "Hombro Frontal": 0.10},
    "Press de Banca con Mancuernas": {"Pecho": 0.80, "Tríceps": 0.10, "Hombro Frontal": 0.10},
    "Press Inclinado con Mancuernas": {"Pecho Superior": 0.70, "Hombro Frontal": 0.20, "Tríceps": 0.10},
    "Aperturas con Mancuernas": {"Pecho": 0.90, "Hombro Frontal": 0.10},
    "Aperturas Inclinadas": {"Pecho Superior": 0.90, "Hombro Frontal": 0.10},
    "Pull-Over con Mancuerna": {"Pecho": 0.50, "Espalda": 0.30, "Tríceps": 0.20},
    "Fondos en Paralelas (Pecho)": {"Pecho Inferior": 0.60, "Tríceps": 0.30, "Hombro Frontal": 0.10},
    "Cruce de Poleas": {"Pecho": 0.90, "Hombro Frontal": 0.10},
    "Cruce de Poleas Bajo (Ascendente)": {"Pecho Superior": 0.90, "Hombro Frontal": 0.10},
    "Pec Deck (Máquina)": {"Pecho": 1.0},
    "Press de Pecho en Máquina": {"Pecho": 0.80, "Tríceps": 0.20},
    "Flexiones (Push-ups)": {"Pecho": 0.60, "Tríceps": 0.30, "Hombro Frontal": 0.10},
    "Flexiones Declinadas": {"Pecho Superior": 0.60, "Hombro Frontal": 0.20, "Tríceps": 0.20},

    # --- ESPALDA (15) ---
    "Dominadas Pronas (Pull-ups)": {"Espalda": 0.70, "Bíceps": 0.20, "Antebrazo": 0.10},
    "Dominadas Supinas (Chin-ups)": {"Espalda": 0.50, "Bíceps": 0.40, "Antebrazo": 0.10},
    "Dominadas Neutras": {"Espalda": 0.60, "Bíceps": 0.30, "Antebrazo": 0.10},
    "Remo con Barra": {"Espalda": 0.60, "Espalda Baja": 0.15, "Bíceps": 0.15, "Trapecio": 0.10},
    "Remo T con Barra": {"Espalda": 0.65, "Bíceps": 0.15, "Trapecio": 0.20},
    "Remo con Mancuerna a una Mano": {"Espalda": 0.70, "Bíceps": 0.20, "Hombro Posterior": 0.10},
    "Jalón al Pecho (Polea)": {"Espalda": 0.75, "Bíceps": 0.25},
    "Remo en Polea Baja": {"Espalda": 0.70, "Bíceps": 0.20, "Trapecio": 0.10},
    "Remo en Máquina": {"Espalda": 0.80, "Bíceps": 0.20},
    "Pull-Over en Polea Alta": {"Espalda": 0.90, "Tríceps": 0.10},
    "Peso Muerto Tradicional": {"Isquiosurales": 0.40, "Espalda Baja": 0.30, "Glúteo": 0.15, "Trapecio": 0.15},
    "Rack Pulls": {"Espalda Baja": 0.40, "Trapecio": 0.40, "Espalda": 0.20},
    "Hiperextensiones": {"Espalda Baja": 0.70, "Isquiosurales": 0.20, "Glúteo": 0.10},
    "Remo Pendlay": {"Espalda": 0.70, "Espalda Baja": 0.20, "Bíceps": 0.10},
    "Encogimientos invertidos (Hombro post/Espalda)": {"Espalda": 0.50, "Hombro Posterior": 0.50},

    # --- PIERNAS Y GLÚTEO (20) ---
    "Sentadilla Libre (Back Squat)": {"Cuádriceps": 0.60, "Glúteo": 0.30, "Espalda Baja": 0.10},
    "Sentadilla Frontal": {"Cuádriceps": 0.80, "Glúteo": 0.10, "Core": 0.10},
    "Sentadilla Búlgara": {"Cuádriceps": 0.50, "Glúteo": 0.40, "Isquiosurales": 0.10},
    "Sentadilla Hack (Máquina)": {"Cuádriceps": 0.80, "Glúteo": 0.20},
    "Sentadilla Sissy": {"Cuádriceps": 0.90, "Core": 0.10},
    "Prensa de Piernas": {"Cuádriceps": 0.70, "Glúteo": 0.20, "Isquiosurales": 0.10},
    "Zancadas (Lunges) con Mancuernas": {"Cuádriceps": 0.50, "Glúteo": 0.40, "Isquiosurales": 0.10},
    "Extensiones de Cuádriceps": {"Cuádriceps": 1.0},
    "Peso Muerto Rumano (RDL)": {"Isquiosurales": 0.60, "Glúteo": 0.30, "Espalda Baja": 0.10},
    "Peso Muerto Piernas Rígidas": {"Isquiosurales": 0.70, "Espalda Baja": 0.30},
    "Peso Muerto Sumo": {"Cuádriceps": 0.40, "Glúteo": 0.40, "Adductores": 0.20},
    "Curl de Pierna Acostado": {"Isquiosurales": 1.0},
    "Curl de Pierna Sentado": {"Isquiosurales": 1.0},
    "Hip Thrust (Empuje de Cadera)": {"Glúteo": 0.80, "Isquiosurales": 0.20},
    "Glute Bridge": {"Glúteo": 0.90, "Isquiosurales": 0.10},
    "Patada de Glúteo en Polea": {"Glúteo": 1.0},
    "Abductores en Máquina": {"Glúteo Medio": 1.0},
    "Adductores en Máquina": {"Adductores": 1.0},
    "Elevación de Talones de Pie": {"Pantorrilla": 1.0},
    "Elevación de Talones Sentado (Costurera)": {"Pantorrilla (Sóleo)": 1.0},

    # --- HOMBROS Y TRAPECIO (12) ---
    "Press Militar con Barra": {"Hombro Frontal": 0.50, "Hombro Medio": 0.20, "Tríceps": 0.20, "Trapecio": 0.10},
    "Press de Hombros con Mancuernas": {"Hombro Frontal": 0.40, "Hombro Medio": 0.40, "Tríceps": 0.20},
    "Press Arnold": {"Hombro Frontal": 0.40, "Hombro Medio": 0.40, "Tríceps": 0.20},
    "Push Press": {"Hombro Frontal": 0.40, "Cuádriceps": 0.30, "Tríceps": 0.20, "Trapecio": 0.10},
    "Elevaciones Laterales con Mancuernas": {"Hombro Medio": 0.90, "Trapecio": 0.10},
    "Elevaciones Laterales en Polea": {"Hombro Medio": 1.0},
    "Elevaciones Frontales con Disco/Mancuerna": {"Hombro Frontal": 1.0},
    "Pájaros con Mancuernas (Hombro Posterior)": {"Hombro Posterior": 0.80, "Trapecio": 0.20},
    "Face Pull en Polea": {"Hombro Posterior": 0.50, "Trapecio": 0.30, "Manguito Rotador": 0.20},
    "Remo al Mentón (Upright Row)": {"Hombro Medio": 0.50, "Trapecio": 0.50},
    "Encogimientos con Barra (Shrugs)": {"Trapecio": 1.0},
    "Encogimientos con Mancuernas": {"Trapecio": 1.0},

    # --- BRAZOS (16) ---
    "Curl con Barra Recta": {"Bíceps": 0.90, "Antebrazo": 0.10},
    "Curl con Barra Z": {"Bíceps": 0.95, "Antebrazo": 0.05},
    "Curl Alterno con Mancuernas": {"Bíceps": 0.90, "Antebrazo": 0.10},
    "Curl Martillo con Mancuernas": {"Bíceps": 0.50, "Antebrazo": 0.50},
    "Curl Concentrado": {"Bíceps": 1.0},
    "Curl en Banco Predicador": {"Bíceps": 1.0},
    "Curl en Polea Baja": {"Bíceps": 1.0},
    "Curl Araña (Spider Curl)": {"Bíceps": 1.0},
    "Press Francés (Rompecráneos)": {"Tríceps": 0.90, "Hombro Frontal": 0.10},
    "Extensión Copa con Mancuerna": {"Tríceps": 1.0},
    "Extensión de Tríceps en Polea (Cuerda)": {"Tríceps": 1.0},
    "Extensión de Tríceps en Polea (Barra V)": {"Tríceps": 1.0},
    "Patada de Tríceps con Mancuerna": {"Tríceps": 1.0},
    "Fondos entre Bancos (Tríceps)": {"Tríceps": 0.80, "Hombro Frontal": 0.20},
    "Curl de Muñeca Supino": {"Antebrazo": 1.0},
    "Curl de Muñeca Prono": {"Antebrazo": 1.0},

    # --- CORE Y ABDOMEN (10) ---
    "Crunch Abdominal Tradicional": {"Abdomen": 1.0},
    "Elevación de Piernas Colgado": {"Abdomen Inferior": 0.70, "Flexores de Cadera": 0.30},
    "Elevación de Piernas Acostado": {"Abdomen Inferior": 0.60, "Flexores de Cadera": 0.40},
    "Rueda Abdominal (Ab Wheel)": {"Abdomen": 0.80, "Espalda Baja": 0.10, "Hombro Frontal": 0.10},
    "Plancha Isométrica (Plank)": {"Core": 0.70, "Hombro Frontal": 0.30},
    "Plancha Lateral": {"Oblicuos": 0.80, "Core": 0.20},
    "Russian Twists con Peso": {"Oblicuos": 0.70, "Core": 0.30},
    "Crunch en Polea Alta": {"Abdomen": 1.0},
    "Leñadores en Polea (Woodchoppers)": {"Oblicuos": 0.80, "Core": 0.20},
    "Toes to Bar (Pies a la Barra)": {"Abdomen Inferior": 0.60, "Core": 0.20, "Espalda": 0.20},

    # --- CALISTENIA DE ALTO NIVEL (7) ---
    "Muscle-Up": {"Espalda": 0.40, "Pecho": 0.30, "Tríceps": 0.20, "Bíceps": 0.10},
    "Fondos en Anillas": {"Pecho Inferior": 0.50, "Tríceps": 0.30, "Core": 0.20},
    "Pino (Handstand Push-up)": {"Hombro Frontal": 0.70, "Tríceps": 0.20, "Core": 0.10},
    "Progresión Front Lever": {"Espalda": 0.60, "Core": 0.40},
    "Progresión Back Lever": {"Espalda Baja": 0.40, "Hombro Posterior": 0.30, "Core": 0.30},
    "L-Sit (Isométrico)": {"Abdomen Inferior": 0.60, "Tríceps": 0.20, "Cuádriceps": 0.20},
    "Pistol Squat (Sentadilla a 1 Pierna)": {"Cuádriceps": 0.60, "Glúteo": 0.20, "Core": 0.20},

    # --- ACONDICIONAMIENTO DE COMBATE / TÁCTICO (5) ---
    "Sombra Lastrada con Mancuernas": {"Hombro Frontal": 0.40, "Espalda": 0.30, "Tríceps": 0.15, "Core": 0.15},
    "Golpeo en Costal Pesado (Heavy Bag)": {"Hombro Frontal": 0.30, "Espalda": 0.30, "Pecho": 0.20, "Core": 0.20},
    "Pateo en Thai Pads": {"Cuádriceps": 0.40, "Glúteo": 0.30, "Core": 0.30},
    "Clinch Isométrico con Banda/Polea": {"Espalda": 0.50, "Trapecio": 0.30, "Bíceps": 0.20},
    "Sprawls / Burpees": {"Core": 0.40, "Pecho": 0.20, "Cuádriceps": 0.20, "Hombro Frontal": 0.20}
}

CATALOGO_GRUPOS_MUSCULARES = {
    "Pecho": {"Pecho": 0.80, "Tríceps": 0.10, "Hombro Frontal": 0.10},
    "Espalda": {"Espalda": 0.80, "Bíceps": 0.20},
    "Pierna": {"Cuádriceps": 0.40, "Isquiosurales": 0.40, "Glúteo": 0.20},
    "Hombro": {"Hombro Medio": 0.50, "Hombro Frontal": 0.30, "Hombro Posterior": 0.20},
    "Brazo": {"Bíceps": 0.50, "Tríceps": 0.50},
    "Core": {"Abdomen": 0.80, "Espalda Baja": 0.20}
}

FACTOR_MUSCULO = {
    "Pierna": 1.0,     # Músculos gigantes (Sentadilla) se miden normal
    "Espalda": 1.2,
    "Pecho": 1.2,
    "Hombro": 2.0,     # Músculos medianos
    "Brazo": 3.0,      # Bíceps y Tríceps reciben un buff x3 en su cálculo
    "Antebrazo": 4.0,  # Músculos diminutos reciben un buff x4
    "Pantorrilla": 3.0
}

# --- LORE HISTÓRICO Y MITOLÓGICO POR NIVELES (1 - 25) ---
LORE_HISTORICO = {
    1: {"M": "[Sistema] Despertar completado. Eres un Cazador Rango E. Tus estadísticas físicas base son las de un civil.", 
        "F": "[Sistema] Despertar completado. Eres una Cazadora Rango E. Tus estadísticas físicas base son las de un civil."},
    2: {"M": "[Sistema] Misión diaria registrada. Tus fibras musculares empiezan a adaptarse a la carga. Abandonando fragilidad.", 
        "F": "[Sistema] Misión diaria registrada. Tu cuerpo empieza a mutar bajo la presión. Abandonando debilidad mortal."},
    3: {"M": "[Sistema] Fuerza incrementada. Ya tienes el nivel para sobrevivir a un Calabozo Rango E sin grupo de asalto.", 
        "F": "[Sistema] Fuerza incrementada. Ya tienes el nivel para sobrevivir a un Calabozo Rango E como vanguardia."},
    4: {"M": "[Sistema] Tu sistema nervioso está traduciendo el daño muscular en potencia bruta. Los cristales de maná reaccionan a ti.", 
        "F": "[Sistema] Tu sistema nervioso traduce el daño en pura potencia. La energía mágica empieza a rodear tu cuerpo."},
    5: {"M": "[Sistema] ¡Ascenso a Rango D! Tienes la fuerza suficiente para enfrentar bestias mágicas menores cuerpo a cuerpo.", 
        "F": "[Sistema] ¡Ascenso a Rango D! Tu fuerza de impacto ya es capaz de quebrar el exoesqueleto de bestias mágicas menores."},
    6: {"M": "[Sistema] Densidad muscular aumentada. Tus golpes contundentes ya pueden abollar armaduras de bajo grado.", 
        "F": "[Sistema] Densidad muscular aumentada. Tus ataques físicos tienen la inercia necesaria para derribar monstruos pesados."},
    7: {"M": "[Sistema] Tu umbral de fatiga se ha roto. Puedes mantener el combate prolongado dentro del calabozo sin agotarte.", 
        "F": "[Sistema] Tu umbral de dolor ha sido reescrito. Eres capaz de sostener el combate frontal en zonas de alta densidad mágica."},
    8: {"M": "[Sistema] Eres la punta de lanza. Los gremios menores empezarían a pelearse por reclutarte en sus incursiones.", 
        "F": "[Sistema] Eres la pieza central del asalto. Tu presencia física asegura la supervivencia de la retaguardia."},
    9: {"M": "[Sistema] Veteranía confirmada. Tus músculos y tendones cuentan la historia de decenas de calabozos cerrados.", 
        "F": "[Sistema] Veteranía confirmada. Tu biomecánica está optimizada exclusivamente para la cacería y la destrucción."},
    10: {"M": "[Sistema] ¡Ascenso a Rango C! Fuerza destructiva detectada. Eres un veterano reconocido. La magia fluye con tu fuerza física.", 
         "F": "[Sistema] ¡Ascenso a Rango C! Fuerza destructiva detectada. Tu capacidad de combate ya es un riesgo para monstruos intermedios."},
    11: {"M": "[Sistema] Tienes la fuerza de tracción para detener el avance de un jefe de calabozo Rango C con tus propias manos.", 
         "F": "[Sistema] Tienes la fuerza estática para bloquear los ataques pesados de un jefe de calabozo sin retroceder un milímetro."},
    12: {"M": "[Sistema] Alerta: Tu fuerza de empuje ha excedido los límites humanos convencionales. Eres un tanque andante.", 
         "F": "[Sistema] Alerta: Tu resistencia al ácido láctico no es normal. Tu cuerpo se recupera en pleno fragor de la batalla."},
    13: {"M": "[Sistema] Habilidad pasiva desbloqueada: Sed de Sangre. Levantas cargas masivas impulsado por el instinto de cacería.", 
         "F": "[Sistema] Habilidad pasiva desbloqueada: Dominio del Combate. Levantas cargas brutales con una precisión letal."},
    14: {"M": "[Sistema] Eres el escudo del Gremio. Tienes la potencia explosiva para romper formaciones de monstruos pesados.", 
         "F": "[Sistema] Eres el arma de asedio del Gremio. Tu fuerza explosiva atraviesa las defensas mágicas de un solo impacto."},
    15: {"M": "[Sistema] ¡Ascenso a Rango B! Has reescrito las reglas. Tus músculos manejan tonelajes que destrozarían huesos comunes.", 
         "F": "[Sistema] ¡Ascenso a Rango B! Has mutado más allá de lo biológico. Soportas tonelajes que harían colapsar a otros cazadores."},
    16: {"M": "[Sistema] Eres la fuerza principal (Main Force) de cualquier gremio élite. Tu presencia intimida a la magia del entorno.", 
         "F": "[Sistema] Eres la vanguardia absoluta. Las bestias mágicas de bajo nivel huyen al sentir tu densidad de maná y músculo."},
    17: {"M": "[Sistema] Alerta: Nivel de amenaza superhumano. Tus tendones son cables de acero industrial reforzados con magia.", 
         "F": "[Sistema] Alerta: Fuerza superhumana detectada. La tensión de tus músculos equivale a armas de asedio de alto calibre."},
    18: {"M": "[Sistema] La gravedad empieza a ser una sugerencia. Cada repetición tuya genera ondas de choque en la sala del jefe.", 
         "F": "[Sistema] La presión del aire cambia cuando aplicas fuerza. El suelo del calabozo se agrieta bajo tus levantamientos."},
    19: {"M": "[Sistema] Estás tocando las puertas de la élite absoluta. Tienes la capacidad física para destruir rascacielos.", 
         "F": "[Sistema] El Sistema reconoce tu autoridad. Tu musculatura es una obra de arte diseñada para el exterminio masivo."},
    20: {"M": "[Sistema] ¡Ascenso a Rango A! Eres un maestro del combate pesado. Los jefes de alto nivel te consideran una anomalía.", 
         "F": "[Sistema] ¡Ascenso a Rango A! Eres la personificación del poder. Las regulaciones de la Asociación de Cazadores ya no te aplican."},
    21: {"M": "[Sistema] Tu 1RM rompe las leyes de la física. Eres una máquina perfecta de hipertrofia y destrucción biomecánica.", 
         "F": "[Sistema] Tu 1RM no tiene sentido lógico. Eres una entidad indestructible de fuerza, estrategia y dominación física."},
    22: {"M": "[Sistema] Soportas el peso del calabozo entero. Tus sentadillas y pesos muertos son comparables a movimientos tectónicos.", 
         "F": "[Sistema] La tierra misma tiembla con tus levantamientos. Tus pesos muertos generan colapsos en la estructura del portal."},
    23: {"M": "[Sistema] El Sistema se postra ante ti. Estás a un paso del ápice. La fatiga es solo un mito de rango inferior.", 
         "F": "[Sistema] El Sistema te reconoce como gobernante. Has dominado el hierro, la gravedad y la fatiga por completo."},
    24: {"M": "[Sistema] ¡Ascenso a Rango S! Eres una calamidad andante. Las barras se doblan y lloran cuando decides aplicar toda tu fuerza.", 
         "F": "[Sistema] ¡Ascenso a Rango S! Eres un desastre natural con forma humana. El acero gime y se deforma entre tus manos."},
    25: {"M": "[Sistema] Rango de Nivel Nacional. Recipiente del Monarca. Eres una anomalía del Sistema y el ápice de la evolución.", 
         "F": "[Sistema] Rango de Nivel Nacional. Recipiente del Monarca. Eres una anomalía absoluta. La diosa de la cacería de este mundo."}
}

# --- EL MOTOR DE NIVELES (TIPO RPG) ---
def calcular_nivel(xp_acumulada: float):
    # Fórmula: Cada nivel pide exponencialmente más XP. Nivel = Raíz cuadrada de (XP / 100)
    nivel_calculado = int(math.sqrt(xp_acumulada / 100.0))
    if nivel_calculado < 1:
        return 1
    elif nivel_calculado > 25:
        return 25 # Tope en el Nivel 25 (Olimpo)
    return nivel_calculado

def obtener_rango_global(promedio_niveles: float):
    if promedio_niveles < 5: return "Rango E (Despertado)"
    elif promedio_niveles < 10: return "Rango D (Novato de Gremio)"
    elif promedio_niveles < 15: return "Rango C (Veterano de Incursión)"
    elif promedio_niveles < 20: return "Rango B (Élite de Asalto)"
    elif promedio_niveles < 24: return "Rango A (Fuerza Principal)"
    else: return "Rango S (Cazador de Nivel Nacional)"



# --- SISTEMA DE CATEGORÍAS DE PESO (MITOLOGÍA) ---
def obtener_categoria_peso(peso_kg: float):
    if peso_kg < 65: return "Hermes (Ligero)"
    elif peso_kg < 75: return "Apolo (Welter)"
    elif peso_kg < 85: return "Aquiles (Medio)"
    elif peso_kg < 100: return "Ares (Semi-Pesado)"
    else: return "Minotauro (Pesado)"

@app.get("/")
def estado_servidor():
    return {"estatus": "Servidor SIF activo", "mensaje": "Esperando inyeccion de datos"}

@app.post("/registrar_entrenamiento")
def registrar(datos: Entrenamiento, db: Session = Depends(get_db)):
    
    # 0. Buscamos al usuario para saber su género
    usuario = db.query(models.Usuario).filter(models.Usuario.id == datos.usuario_id).first()
    if not usuario:
        return {"estatus": "error", "mensaje": "El Cazador no existe en el Sistema."}
    
    # 1. Estandarización a Kilos
    if datos.unidad == "lb":
        peso_estandar = datos.peso * 0.453592
    else:
        peso_estandar = datos.peso 
        
    tonelaje_interno_kg = peso_estandar * datos.repeticiones * datos.series
    
    # 2. CÁLCULO DE 1RM Y JUSTICIA BIOMECÁNICA
    calculo_1rm_kg = peso_estandar * (1 + (datos.repeticiones / 30.0))
    factor = FACTOR_MUSCULO.get(datos.grupo_muscular, 1.0)
    fuerza_ajustada = calculo_1rm_kg * factor
    
    multiplicador_fuerza = fuerza_ajustada / datos.peso_corporal_kg
    xp_base_total = tonelaje_interno_kg * multiplicador_fuerza

    # 3. EL FILTRO INTELIGENTE
    if datos.ejercicio in CATALOGO_EJERCICIOS:
        distribucion = CATALOGO_EJERCICIOS[datos.ejercicio]
    elif datos.grupo_muscular in CATALOGO_GRUPOS_MUSCULARES:
        distribucion = CATALOGO_GRUPOS_MUSCULARES[datos.grupo_muscular]
    else:
        distribucion = {"General": 1.0}
    
    # 4. REPARTIMOS XP, SUBIMOS DE NIVEL Y SACAMOS EL LORE
    progreso_musculos = {}
    for nombre_musculo, porcentaje in distribucion.items():
        xp_ganada = round(xp_base_total * porcentaje, 2)
        
        musculo_db = db.query(models.MusculoXP).filter(
            models.MusculoXP.usuario_id == datos.usuario_id,
            models.MusculoXP.grupo_muscular == nombre_musculo
        ).first()
        
        if musculo_db:
            musculo_db.xp_acumulada_kg += xp_ganada
        else:
            musculo_db = models.MusculoXP(
                usuario_id=datos.usuario_id,
                grupo_muscular=nombre_musculo,
                xp_acumulada_kg=xp_ganada,
                nivel=1
            )
            db.add(musculo_db)
            
        # ¡Magia del Motor RPG! Calculamos el nuevo nivel
        nivel_nuevo = calcular_nivel(musculo_db.xp_acumulada_kg)
        musculo_db.nivel = nivel_nuevo
        
        progreso_musculos[nombre_musculo] = {
            "xp_ganada": xp_ganada,
            "nivel_actual": nivel_nuevo,
            "mensaje_sistema": LORE_HISTORICO.get(nivel_nuevo, LORE_HISTORICO[25])[usuario.genero]
        }
            
    # 5. REGISTRO EN LA BITÁCORA DEL TIEMPO
    nuevo_registro_historial = models.HistorialEntrenamiento(
        usuario_id=datos.usuario_id,
        ejercicio=datos.ejercicio,
        carga_xp=xp_base_total
    )
    db.add(nuevo_registro_historial)
    db.commit()
    
    # 6. CALCULAMOS EL RANGO GLOBAL
    todos_los_musculos = db.query(models.MusculoXP).filter(
        models.MusculoXP.usuario_id == datos.usuario_id
    ).all()
    
    promedio_niveles = sum(m.nivel for m in todos_los_musculos) / len(todos_los_musculos) if todos_los_musculos else 1.0
    rango_global = obtener_rango_global(promedio_niveles)
    
    return {
        "estatus": "Entrenamiento Registrado",
        "rango_global_actualizado": rango_global,
        "estadisticas_combate": {
            "multiplicador_aplicado": round(multiplicador_fuerza, 2),
            "tonelaje_interno": round(xp_base_total, 2)
        },
        "reporte_musculos": progreso_musculos
    }

@app.get("/cazador/{usuario_id}/perfil")
def ver_perfil_cazador(usuario_id: int, db: Session = Depends(get_db)):
    usuario = db.query(models.Usuario).filter(models.Usuario.id == usuario_id).first()
    if not usuario:
        return {"estatus": "error", "mensaje": "Cazador no encontrado"}
        
    musculos = db.query(models.MusculoXP).filter(models.MusculoXP.usuario_id == usuario_id).all()
    if not musculos:
        return {"cazador": usuario.nombre, "rango_global": "Rango E (Despertado)", "mensaje": LORE_HISTORICO[1][usuario.genero]}
        
    # --- SISTEMA DE ATROFIA MUSCULAR (Decaimiento Exponencial) ---
    ultimo_entrenamiento = db.query(models.HistorialEntrenamiento).filter(
        models.HistorialEntrenamiento.usuario_id == usuario_id
    ).order_by(models.HistorialEntrenamiento.fecha_hora.desc()).first()

    dias_inactivo = 0
    factor_atrofia = 1.0
    
    if ultimo_entrenamiento:
        ahora = datetime.datetime.now(datetime.timezone.utc)
        fecha_ultima = ultimo_entrenamiento.fecha_hora.replace(tzinfo=datetime.timezone.utc) if ultimo_entrenamiento.fecha_hora.tzinfo is None else ultimo_entrenamiento.fecha_hora
        dias_inactivo = (ahora - fecha_ultima).total_seconds() / (24 * 3600)
        
        # Si pasan 15 días, pierde 2.5% de XP por cada día extra de inactividad
        if dias_inactivo >= 15:
            dias_penalizados = int(dias_inactivo) - 15
            factor_atrofia = (1 - 0.025) ** dias_penalizados

    mapa_musculos = {}
    suma_niveles = 0
    
    for m in musculos:
        # Aplicamos la merma metabólica a la XP real
        xp_efectiva = m.xp_acumulada_kg * factor_atrofia
        nivel_efectivo = calcular_nivel(xp_efectiva)
        
        suma_niveles += nivel_efectivo
        mapa_musculos[m.grupo_muscular] = {"nivel": nivel_efectivo, "xp": round(xp_efectiva, 2)}
        
    promedio_niveles = suma_niveles / len(musculos)
    rango_actual = obtener_rango_global(promedio_niveles)
    nivel_general_entero = int(promedio_niveles)
    
    return {
        "cazador": usuario.nombre,
        "rango_global": rango_actual,
        "nivel_promedio": round(promedio_niveles, 1),
        "estatus_sistema": LORE_HISTORICO.get(nivel_general_entero, LORE_HISTORICO[25])[usuario.genero],
        "musculos": mapa_musculos
    }

@app.get("/estamina/{usuario_id}")
def calcular_estamina(usuario_id: int, db: Session = Depends(get_db)):
    usuario = db.query(models.Usuario).filter(models.Usuario.id == usuario_id).first()
    if not usuario: return {"estatus": "error"}
        
    historial = db.query(models.HistorialEntrenamiento).filter(
        models.HistorialEntrenamiento.usuario_id == usuario_id
    ).order_by(models.HistorialEntrenamiento.fecha_hora.desc()).all()
    
    if not historial: return {"diagnostico": "Fresco, sin experiencia.", "estamina": 0.0, "dias_inactivo": 0}
        
    ahora = datetime.datetime.now(datetime.timezone.utc)
    condicion_total = 0.0
    fatiga_total = 0.0
    
    # Extraemos el último entrenamiento real para mandar los días inactivos a la alerta roja del HTML
    ultimo_ent = historial[0]
    fecha_ultima = ultimo_ent.fecha_hora.replace(tzinfo=datetime.timezone.utc) if ultimo_ent.fecha_hora.tzinfo is None else ultimo_ent.fecha_hora
    dias_inactivo = (ahora - fecha_ultima).total_seconds() / (24 * 3600)
    
    for registro in historial:
        fecha_registro = registro.fecha_hora.replace(tzinfo=datetime.timezone.utc) if registro.fecha_hora.tzinfo is None else registro.fecha_hora
        dias_pasados = (ahora - fecha_registro).total_seconds() / (24 * 3600)
        carga = registro.carga_xp
        condicion_total += carga * math.exp(-dias_pasados / usuario.tau_1)
        fatiga_total += carga * math.exp(-dias_pasados / usuario.tau_2)
        
    rendimiento_neto = condicion_total - fatiga_total
    
    if fatiga_total > condicion_total: estado_cazador = "⚠️ Sistema Sobrecargado"
    elif rendimiento_neto > 0 and fatiga_total < (condicion_total * 0.3): estado_cazador = "⚡ ¡Condición Óptima!"
    else: estado_cazador = "🔋 En recuperación activa."
        
    return {
        "diagnostico": estado_cazador, 
        "estamina": round(rendimiento_neto, 2),
        "dias_inactivo": int(dias_inactivo) # <-- Esto dispara el catabolismo en tu HTML
    }