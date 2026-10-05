from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# 1. Definimos que usaremos SQLite y nombramos el archivo físico
SQLALCHEMY_DATABASE_URL = "postgresql://postgres.alwdlkbwfdblkwhzlkvi:B19852217j2217WinnJustinCiencia22Aleluya@aws-0-us-west-2.pooler.supabase.com:6543/postgres"

# 2. Encendemos el motor (connect_args es un requisito de seguridad para SQLite)
engine = create_engine(SQLALCHEMY_DATABASE_URL)

# 3. Creamos la "fábrica de sesiones" para que nuestra app pueda guardar y leer datos
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 4. Creamos la base de donde nacerán todas nuestras tablas (Usuarios, Músculos, etc.)
Base = declarative_base()