from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "Módulo de Valoración Docente con Controles Antisesgo (v0.2)"
    VERSION: str = "0.2.0"
    ALLOWED_EMAIL_DOMAIN: str = "udea.edu.co"
    MIN_RESPUESTAS_PUBLICACION: int = 5
    CONTROL_DB_URL: str = "postgresql://postgres:postgres@localhost:5432/bd_control_supabase"
    RESPUESTAS_DB_URL: str = "postgresql://postgres:postgres@localhost:5432/bd_respuestas_neon"
    MODEL_PATH: str = "../ml/artifacts/modelo_calidad_v1.joblib"
    SUPABASE_URL: str = ""
    SUPABASE_ANON_KEY: str = ""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()

