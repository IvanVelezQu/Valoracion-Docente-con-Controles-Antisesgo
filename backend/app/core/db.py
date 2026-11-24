from sqlalchemy import create_engine, text
from app.core.config import settings

# Una conexión por cada base: identidad (Supabase) y respuestas (Neon) separadas
engine_control = create_engine(settings.CONTROL_DB_URL, pool_pre_ping=True)
engine_respuestas = create_engine(settings.RESPUESTAS_DB_URL, pool_pre_ping=True)