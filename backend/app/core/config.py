from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict

_DEFAULT_CONTROL_DB_URL = "postgresql://postgres:postgres@localhost:5432/bd_control_supabase"
_DEFAULT_RESPUESTAS_DB_URL = "postgresql://postgres:postgres@localhost:5432/bd_respuestas_neon"


class Settings(BaseSettings):
    PROJECT_NAME: str = "Módulo de Valoración Docente con Controles Antisesgo (v0.2)"
    VERSION: str = "0.2.0"
    ALLOWED_EMAIL_DOMAIN: str = "udea.edu.co"
    MIN_RESPUESTAS_PUBLICACION: int = 5
    CONTROL_DB_URL: str = _DEFAULT_CONTROL_DB_URL
    RESPUESTAS_DB_URL: str = _DEFAULT_RESPUESTAS_DB_URL
    USE_IN_MEMORY_DB: Optional[bool] = None
    MODEL_PATH: str = "../ml/artifacts/modelo_calidad_v1.joblib"
    SUPABASE_URL: str = ""
    SUPABASE_ANON_KEY: str = ""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @property
    def usando_bd_real(self) -> bool:
        if self.USE_IN_MEMORY_DB is not None:
            return not self.USE_IN_MEMORY_DB
        return (
            bool(self.CONTROL_DB_URL)
            and bool(self.RESPUESTAS_DB_URL)
            and self.CONTROL_DB_URL != _DEFAULT_CONTROL_DB_URL
            and self.RESPUESTAS_DB_URL != _DEFAULT_RESPUESTAS_DB_URL
        )


settings = Settings()
