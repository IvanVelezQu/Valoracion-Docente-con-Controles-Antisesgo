-- =============================================================================
-- BD DE RESPUESTAS ANÓNIMAS (Neon - PostgreSQL)
-- Propósito: Almacenar envíos anónimos del instrumento v0.2, fichas de hechos
-- del curso, señales del motor de calidad y pesos estadísticos.
-- REGLA (RNF-03): Las respuestas de v0.2 nunca se mezclan con versiones previas (v0.1).
-- =============================================================================

CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- 1. Ficha de hechos objetivos del curso (aportada por docente o plataforma Ude@/Moodle)
CREATE TABLE IF NOT EXISTS fichas_hechos_curso (
    curso_codigo VARCHAR(32) NOT NULL,
    semestre VARCHAR(10) NOT NULL DEFAULT '2026-2',
    ref_01_plazo_cumplido BOOLEAN NOT NULL,      -- ¿Devolvió calificaciones en el plazo establecido?
    ref_02_programa_detallado BOOLEAN NOT NULL,  -- ¿El programa detallaba criterios de evaluación?
    ref_03_asesorias_cumplidas BOOLEAN NOT NULL, -- ¿Se cumplieron los horarios de asesoría publicados?
    dias_promedio_calificacion NUMERIC(4,1),
    fecha_actualizacion DATE NOT NULL DEFAULT CURRENT_DATE,
    PRIMARY KEY (curso_codigo, semestre)
);

-- 2. Envíos anónimos del Instrumento v0.2 (21 ítems: 8 DIM + 13 control)
CREATE TABLE IF NOT EXISTS envios_encuesta_v02 (
    envio_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    curso_codigo VARCHAR(32) NOT NULL,
    semestre VARCHAR(10) NOT NULL DEFAULT '2026-2',
    version_instrumento VARCHAR(10) NOT NULL DEFAULT 'v0.2' CHECK (version_instrumento = 'v0.2'),
    fecha_envio_dia DATE NOT NULL DEFAULT CURRENT_DATE, -- Solo día para impedir reidentificación
    duracion_seg INTEGER NOT NULL CHECK (duracion_seg >= 0),

    -- Bloque Autorreflexión (AR): codificados 1..4 según rango
    ar_01 SMALLINT NOT NULL CHECK (ar_01 BETWEEN 1 AND 4),
    ar_02 SMALLINT NOT NULL CHECK (ar_02 BETWEEN 1 AND 4),
    ar_03 SMALLINT NOT NULL CHECK (ar_03 BETWEEN 1 AND 4),

    -- Bloque Separación Curso/Profesor (SEP)
    sep_01 SMALLINT NOT NULL CHECK (sep_01 BETWEEN 1 AND 5), -- Interés previo 1..5
    sep_02 SMALLINT NOT NULL CHECK (sep_02 IN (0, 1)),       -- Obligatoria: 1=Sí, 0=No
    sep_03 SMALLINT NOT NULL CHECK (sep_03 BETWEEN 1 AND 5), -- Nota esperada (rangos 1..5)

    -- Bloque Dimensiones Docentes (DIM-01 a DIM-08): 0=No aplica, 1..5=Escala frecuencia
    dim_01 SMALLINT NOT NULL CHECK (dim_01 BETWEEN 0 AND 5),
    dim_02 SMALLINT NOT NULL CHECK (dim_02 BETWEEN 0 AND 5),
    dim_03 SMALLINT NOT NULL CHECK (dim_03 BETWEEN 0 AND 5),
    dim_04 SMALLINT NOT NULL CHECK (dim_04 BETWEEN 0 AND 5),
    dim_05 SMALLINT NOT NULL CHECK (dim_05 BETWEEN 0 AND 5),
    dim_06 SMALLINT NOT NULL CHECK (dim_06 BETWEEN 0 AND 5),
    dim_07 SMALLINT NOT NULL CHECK (dim_07 BETWEEN 0 AND 5),
    dim_08 SMALLINT NOT NULL CHECK (dim_08 BETWEEN 0 AND 5),

    -- Bloque Referencia (REF-01 a REF-03): 0=No aplica, 1..5
    ref_01 SMALLINT NOT NULL CHECK (ref_01 BETWEEN 0 AND 5),
    ref_02 SMALLINT NOT NULL CHECK (ref_02 BETWEEN 0 AND 5),
    ref_03 SMALLINT NOT NULL CHECK (ref_03 BETWEEN 0 AND 5),

    -- Bloque Codificación Inversa (INV-01 a INV-04): 0=No aplica, 1..5
    inv_01 SMALLINT NOT NULL CHECK (inv_01 BETWEEN 0 AND 5),
    inv_02 SMALLINT NOT NULL CHECK (inv_02 BETWEEN 0 AND 5),
    inv_03 SMALLINT NOT NULL CHECK (inv_03 BETWEEN 0 AND 5),
    inv_04 SMALLINT NOT NULL CHECK (inv_04 BETWEEN 0 AND 5),

    -- Señales calculadas por Etapa A (Reglas explicables)
    desviacion_inversa_media NUMERIC(5,3) NOT NULL DEFAULT 0.0,
    bandera_inconsistencia_inversa BOOLEAN NOT NULL DEFAULT FALSE,
    bandera_contradiccion_hechos BOOLEAN NOT NULL DEFAULT FALSE,
    bandera_linea_recta BOOLEAN NOT NULL DEFAULT FALSE,
    bandera_demasiado_rapida BOOLEAN NOT NULL DEFAULT FALSE,
    bandera_revision_asesoria BOOLEAN NOT NULL DEFAULT FALSE,
    senal_arrastre_materia BOOLEAN NOT NULL DEFAULT FALSE,
    grupo_baja_exposicion BOOLEAN NOT NULL DEFAULT FALSE,

    -- Salida Etapa B (Clasificador entrenado)
    prob_inconsistente NUMERIC(5,4) NOT NULL DEFAULT 0.0,
    peso_calidad NUMERIC(5,4) NOT NULL DEFAULT 1.0 CHECK (peso_calidad BETWEEN 0.0 AND 1.0),
    aislado BOOLEAN NOT NULL DEFAULT FALSE,
    version_modelo VARCHAR(32) NOT NULL DEFAULT 'modelo_calidad_v1'
);

CREATE INDEX IF NOT EXISTS idx_envios_curso ON envios_encuesta_v02(curso_codigo, semestre);

-- 3. Tabla de agregados nocturnos (Etapa C)
CREATE TABLE IF NOT EXISTS agregados_curso_v02 (
    curso_codigo VARCHAR(32) NOT NULL,
    semestre VARCHAR(10) NOT NULL DEFAULT '2026-2',
    n_total INTEGER NOT NULL,
    n_validas INTEGER NOT NULL,
    porcentaje_aislados NUMERIC(5,2) NOT NULL,
    publicable BOOLEAN NOT NULL GENERATED ALWAYS AS (n_validas >= 5) STORED,
    resumen_dimensiones JSONB NOT NULL, -- Medianas ponderadas, IQR, frecuencias y medias crudas
    fecha_recalculo TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    PRIMARY KEY (curso_codigo, semestre)
);
