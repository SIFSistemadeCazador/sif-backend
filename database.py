from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# 1. Definimos que usaremos SQLite y nombramos el archivo físico
SQLALCHEMY_DATABASE_URL = "sqlite:///./sif_database.db"

# 2. Encendemos el motor (connect_args es un requisito de seguridad para SQLite)
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)

# 3. Creamos la "fábrica de sesiones" para que nuestra app pueda guardar y leer datos
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 4. Creamos la base de donde nacerán todas nuestras tablas (Usuarios, Músculos, etc.)
Base = declarative_base()