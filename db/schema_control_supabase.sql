-- =============================================================================
-- BD DE CONTROL (Supabase - PostgreSQL)
-- Propósito: Validar matrícula (@udea.edu.co) y gestionar la emisión/consumo
-- de tokens por firma ciega RSA (RFC 9474).
-- REGLA DE ARQUITECTURA (RF-04): Esta base de datos NUNCA almacena respuestas
-- ni comparte llaves foráneas o metadatos temporales exactos con la BD de respuestas.
-- =============================================================================

CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- 1. Registro de matrícula por curso (sin vínculo con envíos de encuesta)
CREATE TABLE IF NOT EXISTS matriculas_curso (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    estudiante_email_hash VARCHAR(64) NOT NULL, -- SHA-256 del correo @udea.edu.co
    curso_codigo VARCHAR(32) NOT NULL,
    semestre VARCHAR(10) NOT NULL DEFAULT '2026-2',
    ya_solicito_token BOOLEAN NOT NULL DEFAULT FALSE,
    fecha_emision_dia DATE, -- Solo fecha por día para evitar correlación temporal
    UNIQUE (estudiante_email_hash, curso_codigo, semestre)
);

-- 2. Registro de tokens anónimos consumidos (evita doble votación)
CREATE TABLE IF NOT EXISTS tokens_consumidos (
    token_hash VARCHAR(64) PRIMARY KEY, -- SHA-256 del token descegado firmado
    curso_codigo VARCHAR(32) NOT NULL,
    semestre VARCHAR(10) NOT NULL DEFAULT '2026-2',
    fecha_consumo_dia DATE NOT NULL DEFAULT CURRENT_DATE -- Truncado a día por privacidad
);

CREATE INDEX IF NOT EXISTS idx_tokens_curso ON tokens_consumidos(curso_codigo, semestre);
