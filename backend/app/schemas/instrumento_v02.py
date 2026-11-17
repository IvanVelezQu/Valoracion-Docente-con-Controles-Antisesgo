from typing import Dict, List, Optional
from pydantic import BaseModel, Field, field_validator

# Orden oficial de presentación del Instrumento v0.2 (21 ítems)
# Regla de diseño:
# 1. Autorreflexión (AR-01 a AR-03)
# 2. Separación / Contexto (SEP-01 a SEP-03)
# 3. 8 ítems de dimensión (DIM-01 a DIM-08) intercalados con los 3 de referencia (REF-01 a REF-03)
# 4. 4 ítems inversos (INV-01 a INV-04) al final, cada uno al menos 6 preguntas después de su pareja.
ORDEN_PRESENTACION_V02: List[str] = [
    "AR-01", "AR-02", "AR-03",
    "SEP-01", "SEP-02", "SEP-03",
    "DIM-01", "DIM-02", "REF-02",
    "DIM-03", "DIM-04", "REF-01",
    "DIM-05", "DIM-06", "REF-03",
    "DIM-07", "DIM-08",
    "INV-01", "INV-02", "INV-03", "INV-04"
]

PARES_INVERSOS = [
    ("DIM-01", "INV-01"),
    ("DIM-02", "INV-02"),
    ("DIM-04", "INV-03"),
    ("DIM-05", "INV-04"),
]

class FichaHechosCurso(BaseModel):
    curso_codigo: str
    semestre: str = "2026-2"
    ref_01_plazo_cumplido: bool = Field(..., description="Las actividades calificadas se devolvieron dentro del plazo")
    ref_02_programa_detallado: bool = Field(..., description="El programa publicado detallaba los criterios de evaluación")
    ref_03_asesorias_cumplidas: bool = Field(..., description="Los horarios de asesoría publicados se cumplieron")
    dias_promedio_calificacion: Optional[float] = 5.0

class EnvioEncuestaV02(BaseModel):
    curso_codigo: str = Field(..., min_length=2, max_length=32)
    semestre: str = Field(default="2026-2")
    token_anonimo: str = Field(..., min_length=16, description="Token firmado a ciegas desacoplado de la identidad")
    firma_token: str = Field(..., min_length=16, description="Firma RSA ciega verificable (RFC 9474)")
    duracion_seg: int = Field(..., ge=1, le=7200, description="Tiempo total de respuesta en segundos")

    # Autorreflexión (1: 0-25%, 2: 26-50%, 3: 51-75%, 4: 76-100% | AR-03: 1: 0, 2: 1-2, 3: 3-5, 4: >5)
    AR_01: int = Field(..., ge=1, le=4)
    AR_02: int = Field(..., ge=1, le=4)
    AR_03: int = Field(..., ge=1, le=4)

    # Separación Curso/Profesor
    SEP_01: int = Field(..., ge=1, le=5, description="Interés previo en la materia (1 muy bajo - 5 muy alto)")
    SEP_02: int = Field(..., ge=0, le=1, description="Materia obligatoria (1=Sí, 0=No)")
    SEP_03: int = Field(..., ge=1, le=5, description="Rango de nota esperada (1..5)")

    # Dimensiones Docentes (0 = No aplica, 1..5 escala de frecuencia)
    DIM_01: int = Field(..., ge=0, le=5)
    DIM_02: int = Field(..., ge=0, le=5)
    DIM_03: int = Field(..., ge=0, le=5)
    DIM_04: int = Field(..., ge=0, le=5)
    DIM_05: int = Field(..., ge=0, le=5)
    DIM_06: int = Field(..., ge=0, le=5)
    DIM_07: int = Field(..., ge=0, le=5)
    DIM_08: int = Field(..., ge=0, le=5)

    # Ítems de Referencia verificables a nivel de curso (0 = No aplica, 1..5)
    REF_01: int = Field(..., ge=0, le=5)
    REF_02: int = Field(..., ge=0, le=5)
    REF_03: int = Field(..., ge=0, le=5)

    # Ítems de Codificación Inversa (0 = No aplica, 1..5)
    INV_01: int = Field(..., ge=0, le=5)
    INV_02: int = Field(..., ge=0, le=5)
    INV_03: int = Field(..., ge=0, le=5)
    INV_04: int = Field(..., ge=0, le=5)

class ResultadoMotorCalidad(BaseModel):
    desviacion_inversa_media: float
    desviaciones_pares: Dict[str, float]
    racha_maxima_iguales: int
    proporcion_mismo_valor: float
    desviacion_intraindividual: float
    porcentaje_no_aplica: float
    bandera_inconsistencia_inversa: bool
    bandera_contradiccion_hechos: bool
    bandera_linea_recta: bool
    bandera_demasiado_rapida: bool
    bandera_revision_asesoria: bool
    senal_arrastre_materia: bool
    grupo_baja_exposicion: bool
    prob_inconsistente: float
    peso_calidad: float
    aislado: bool
