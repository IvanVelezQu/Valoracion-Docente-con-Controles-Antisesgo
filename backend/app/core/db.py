import importlib.util
from typing import Optional
from sqlalchemy import Engine, create_engine
from app.core.config import settings


def _normalizar_url_postgres(url: str) -> str:
    """
    Compatible con SQLAlchemy 2.1 + psycopg (Render) y con psycopg2 en entornos locales.
    """
    if url.startswith("postgres://"):
        url = "postgresql://" + url[len("postgres://"):]
    if url.startswith("postgresql://"):
        tiene_psycopg = importlib.util.find_spec("psycopg") is not None
        tiene_psycopg2 = importlib.util.find_spec("psycopg2") is not None
        if not tiene_psycopg and tiene_psycopg2:
            return "postgresql+psycopg2://" + url[len("postgresql://"):]
    return url


# Una conexión por cada base: identidad (Supabase) y respuestas (Neon) separadas
engine_control: Optional[Engine] = (
    create_engine(_normalizar_url_postgres(settings.CONTROL_DB_URL), pool_pre_ping=True)
    if settings.usando_bd_real
    else None
)
engine_respuestas: Optional[Engine] = (
    create_engine(_normalizar_url_postgres(settings.RESPUESTAS_DB_URL), pool_pre_ping=True)
    if settings.usando_bd_real
    else None
)
