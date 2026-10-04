from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from database import Base
import datetime

# Tabla 1: El Perfil del Jugador (Cazador)
class Usuario(Base):
    __tablename__ = "usuarios"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String, index=True)
    genero = Column(String)  # 'M' o 'F' para cambiar la historia mítica/histórica
    
    # Constantes iniciales para el Modelo de Banister (Estamina/Fatiga)
    # El sistema modificará estos valores más adelante para aprender del usuario
    tau_1 = Column(Float, default=15.0)  # Velocidad de adaptación
    tau_2 = Column(Float, default=5.0)   # Velocidad de recuperación de fatiga
    
    # Conexión mágica: Un usuario tiene muchos músculos
    musculos = relationship("MusculoXP", back_populates="dueño")


# Tabla 2: El Mapa Muscular (El Aura y la Experiencia)
class MusculoXP(Base):
    __tablename__ = "musculos_xp"

    id = Column(Integer, primary_key=True, index=True)
    usuario_id = Column(Integer, ForeignKey("usuarios.id")) # Lo vincula al Cazador
    
    grupo_muscular = Column(String, index=True) # Ej: "Pecho", "Cuádriceps"
    nivel = Column(Integer, default=1)          # Todos empiezan en Ilota Nivel 1
    xp_acumulada_kg = Column(Float, default=0.0) # El tonelaje total histórico
    
    # Conexión de regreso para saber de quién es este músculo
    dueño = relationship("Usuario", back_populates="musculos")

class HistorialEntrenamiento(Base):
    __tablename__ = "historial_entrenamiento"

    id = Column(Integer, primary_key=True, index=True)
    usuario_id = Column(Integer, ForeignKey("usuarios.id"))
    
    # Guarda el momento exacto en el que se hizo el ejercicio
    fecha_hora = Column(DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc))
    
    ejercicio = Column(String)
    carga_xp = Column(Float)
