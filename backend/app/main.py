from pathlib import Path
from typing import Any, Dict, List, Optional

from dotenv import load_dotenv

# Carga las variables de entorno antes de importar módulos de la aplicación
BASE_DIR = Path(__file__).resolve().parents[1]
load_dotenv(BASE_DIR / ".env")
load_dotenv()

import numpy as np
from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy import text

from app.core.config import settings
from app.core.db import engine_control, engine_respuestas
from app.schemas.instrumento_v02 import (
    EnvioEncuestaV02,
    FichaHechosCurso,
    ORDEN_PRESENTACION_V02,
)
from app.services.auth_supabase import verificar_usuario_udea
from app.services.firma_ciega import GestorFirmaCiegaSimulado
from app.services.motor_calidad import MotorCalidadAntisesgo

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description=(
        "API de Valoración Docente con Controles Antisesgo (Instrumento v0.2). "
        "Separa físicamente la BD de control (Supabase) y la BD de respuestas (Neon)."
    ),
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

model_path = Path(settings.MODEL_PATH)
if not model_path.is_absolute() and not model_path.exists():
    model_path = (BASE_DIR / settings.MODEL_PATH).resolve()

motor_calidad = MotorCalidadAntisesgo(model_path=str(model_path))
gestor_firma = GestorFirmaCiegaSimulado()

USANDO_BD_REAL = engine_control is not None and engine_respuestas is not None

# Almacenamiento en memoria de respaldo para desarrollo local sin BD externa configurada
BD_CONTROL_EMISIONES: set = set()
BD_CONTROL_TOKENS_USADOS: set = set()
BD_RESPUESTAS_FICHAS: Dict[str, FichaHechosCurso] = {
    "ING-SIS-2026": FichaHechosCurso(
        curso_codigo="ING-SIS-2026",
        semestre="2026-2",
        ref_01_plazo_cumplido=True,
        ref_02_programa_detallado=True,
        ref_03_asesorias_cumplidas=True,
        dias_promedio_calificacion=4.5,
    )
}
BD_RESPUESTAS_ENVIOS: List[Dict[str, Any]] = []


class SolicitudTokenCiego(BaseModel):
    correo_institucional: Optional[EmailStr] = None
    curso_codigo: str = Field(..., min_length=2, max_length=32)
    semestre: str = "2026-2"
    token_cegado: str = Field(..., min_length=16)


@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "instrumento": "v0.2",
        "total_items": len(ORDEN_PRESENTACION_V02),
        "orden_presentacion": ORDEN_PRESENTACION_V02,
        "modelo_cargado": motor_calidad.model is not None,
        "modo_persistencia": "postgresql" if USANDO_BD_REAL else "memoria",
    }


@app.post("/api/v1/auth/solicitar-token-ciego")
async def solicitar_token_ciego(
    req: SolicitudTokenCiego,
    correo_verificado: str = Depends(verificar_usuario_udea),
):
    """
    Paso 1 y 2: Valida el JWT de Supabase (@udea.edu.co) mediante verificar_usuario_udea,
    registra la emisión en la BD de Control (Supabase) y emite firma ciega sin asociar
    el token a las respuestas futuras.
    """
    dominio = correo_verificado.split("@")[-1].lower()
    if dominio != settings.ALLOWED_EMAIL_DOMAIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Solo se permiten cuentas institucionales @{settings.ALLOWED_EMAIL_DOMAIN}",
        )

    if req.correo_institucional and req.correo_institucional.lower() != correo_verificado.lower():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="El correo de la solicitud no coincide con la cuenta institucional autenticada.",
        )

    if USANDO_BD_REAL and engine_control is not None:
        email_hash = gestor_firma.hash_identificador(correo_verificado)
        with engine_control.begin() as conn:
            fila = conn.execute(
                text("""
                    INSERT INTO matriculas_curso
                        (estudiante_email_hash, curso_codigo, semestre, ya_solicito_token, fecha_emision_dia)
                    VALUES (:email_hash, :curso, :semestre, TRUE, CURRENT_DATE)
                    ON CONFLICT (estudiante_email_hash, curso_codigo, semestre) DO NOTHING
                    RETURNING id
                """),
                {"email_hash": email_hash, "curso": req.curso_codigo, "semestre": req.semestre},
            ).first()

        if fila is None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="El estudiante ya solicitó un token anónimo para este curso.",
            )
    else:
        llave_matricula = gestor_firma.hash_identificador(
            f"{correo_verificado}:{req.curso_codigo}:{req.semestre}"
        )
        if llave_matricula in BD_CONTROL_EMISIONES:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="El estudiante ya solicitó un token anónimo para este curso.",
            )
        BD_CONTROL_EMISIONES.add(llave_matricula)

    firma_ciega = gestor_firma.emitir_firma_ciega(req.token_cegado)
    return {
        "curso_codigo": req.curso_codigo,
        "semestre": req.semestre,
        "firma_ciega": firma_ciega,
    }


@app.post("/api/v1/encuestas/enviar", status_code=status.HTTP_201_CREATED)
def recibir_encuesta_anonima(envio: EnvioEncuestaV02):
    """
    Paso 3: Consume atómicamente el token en la BD de Control y almacena la
    respuesta anónima ponderada por el Motor de Calidad en la BD de Respuestas.
    """
    if not gestor_firma.verificar_token_anonimo(envio.token_anonimo, envio.firma_token):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Firma ciega del token inválida.",
        )

    token_hash = gestor_firma.hash_identificador(envio.token_anonimo)

    if USANDO_BD_REAL and engine_control is not None and engine_respuestas is not None:
        # 1. Leer la ficha del curso desde Neon
        with engine_respuestas.connect() as conn:
            f = conn.execute(
                text("""
                    SELECT * FROM fichas_hechos_curso
                    WHERE curso_codigo = :curso AND semestre = :semestre
                """),
                {"curso": envio.curso_codigo, "semestre": envio.semestre},
            ).mappings().first()

        if f:
            ficha = FichaHechosCurso(
                curso_codigo=f["curso_codigo"],
                semestre=f["semestre"],
                ref_01_plazo_cumplido=f["ref_01_plazo_cumplido"],
                ref_02_programa_detallado=f["ref_02_programa_detallado"],
                ref_03_asesorias_cumplidas=f["ref_03_asesorias_cumplidas"],
                dias_promedio_calificacion=float(f["dias_promedio_calificacion"] or 5.0),
            )
        else:
            ficha = FichaHechosCurso(
                curso_codigo=envio.curso_codigo,
                semestre=envio.semestre,
                ref_01_plazo_cumplido=True,
                ref_02_programa_detallado=True,
                ref_03_asesorias_cumplidas=True,
            )

        resultado_calidad = motor_calidad.evaluar_envio(envio, ficha)

        # 2. Marcar el token como usado en Supabase
        with engine_control.begin() as conn:
            usado = conn.execute(
                text("""
                    INSERT INTO tokens_consumidos (token_hash, curso_codigo, semestre)
                    VALUES (:token_hash, :curso, :semestre)
                    ON CONFLICT (token_hash) DO NOTHING
                    RETURNING token_hash
                """),
                {
                    "token_hash": token_hash,
                    "curso": envio.curso_codigo,
                    "semestre": envio.semestre,
                },
            ).first()

        if usado is None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Este token anónimo ya fue utilizado.",
            )

        # 3. Guardar la respuesta anónima en Neon
        datos = envio.model_dump(exclude={"token_anonimo", "firma_token"})
        fila = {k.lower(): v for k, v in datos.items()}
        calidad = resultado_calidad.model_dump()
        for campo in [
            "desviacion_inversa_media",
            "bandera_inconsistencia_inversa",
            "bandera_contradiccion_hechos",
            "bandera_linea_recta",
            "bandera_demasiado_rapida",
            "bandera_revision_asesoria",
            "senal_arrastre_materia",
            "grupo_baja_exposicion",
            "prob_inconsistente",
            "peso_calidad",
            "aislado",
        ]:
            fila[campo] = calidad[campo]

        columnas = ", ".join(fila.keys())
        valores = ", ".join(f":{k}" for k in fila.keys())

        try:
            with engine_respuestas.begin() as conn:
                conn.execute(
                    text(f"INSERT INTO envios_encuesta_v02 ({columnas}) VALUES ({valores})"),
                    fila,
                )
        except Exception:
            with engine_control.begin() as conn:
                conn.execute(
                    text("DELETE FROM tokens_consumidos WHERE token_hash = :t"),
                    {"t": token_hash},
                )
            raise HTTPException(
                status_code=500,
                detail="No se pudo guardar la encuesta. Intenta de nuevo.",
            )
    else:
        if token_hash in BD_CONTROL_TOKENS_USADOS:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Este token anónimo ya fue utilizado.",
            )

        ficha = BD_RESPUESTAS_FICHAS.get(
            envio.curso_codigo,
            FichaHechosCurso(
                curso_codigo=envio.curso_codigo,
                semestre=envio.semestre,
                ref_01_plazo_cumplido=True,
                ref_02_programa_detallado=True,
                ref_03_asesorias_cumplidas=True,
            ),
        )
        resultado_calidad = motor_calidad.evaluar_envio(envio, ficha)
        BD_CONTROL_TOKENS_USADOS.add(token_hash)
        BD_RESPUESTAS_ENVIOS.append({
            "envio": envio.model_dump(exclude={"token_anonimo", "firma_token"}),
            "calidad": resultado_calidad.model_dump(),
        })

    return {
        "mensaje": "Encuesta anónima registrada correctamente (Instrumento v0.2).",
        "version_instrumento": "v0.2",
        "calidad_resumen": {
            "peso_calidad": resultado_calidad.peso_calidad,
            "aislado": resultado_calidad.aislado,
        },
    }


@app.get("/api/v1/dashboard/curso/{curso_codigo}")
def obtener_dashboard_docente(curso_codigo: str, semestre: str = "2026-2"):
    """
    Etapa C: Entrega resultados agregados únicamente si N_válidas >= 5.
    Reporta mediana ponderada por w, distribución de frecuencias (boxplots/barras),
    porcentaje aislado y media cruda como referencia secundaria. Nunca genera rankings.
    """
    if USANDO_BD_REAL and engine_respuestas is not None:
        with engine_respuestas.connect() as conn:
            filas = conn.execute(
                text("""
                    SELECT * FROM envios_encuesta_v02
                    WHERE curso_codigo = :curso AND semestre = :semestre
                """),
                {"curso": curso_codigo, "semestre": semestre},
            ).mappings().all()

        envios_curso = [
            {
                "envio": {k.upper(): v for k, v in r.items()},
                "calidad": {"aislado": r["aislado"], "peso_calidad": float(r["peso_calidad"])},
            }
            for r in filas
        ]
    else:
        envios_curso = [
            r
            for r in BD_RESPUESTAS_ENVIOS
            if r["envio"]["curso_codigo"] == curso_codigo
            and r["envio"]["semestre"] == semestre
        ]

    n_total = len(envios_curso)
    envios_validos = [r for r in envios_curso if not r["calidad"]["aislado"]]
    n_validas = len(envios_validos)

    if n_validas < settings.MIN_RESPUESTAS_PUBLICACION:
        return {
            "curso_codigo": curso_codigo,
            "semestre": semestre,
            "publicable": False,
            "n_total": n_total,
            "n_validas": n_validas,
            "minimo_requerido": settings.MIN_RESPUESTAS_PUBLICACION,
            "mensaje": (
                f"Privacidad protegida: se requieren al menos {settings.MIN_RESPUESTAS_PUBLICACION} "
                f"respuestas válidas para publicar resultados (actualmente: {n_validas})."
            ),
        }

    porcentaje_aislados = round(100.0 * (n_total - n_validas) / max(1, n_total), 2)
    dimensiones_resumen = {}

    for i in range(1, 9):
        dim_key = f"DIM_0{i}"
        valores = [r["envio"][dim_key] for r in envios_curso if r["envio"][dim_key] > 0]
        pesos = [r["calidad"]["peso_calidad"] for r in envios_curso if r["envio"][dim_key] > 0]
        valores_validos = [
            r["envio"][dim_key] for r in envios_validos if r["envio"][dim_key] > 0
        ]

        mediana_pond = MotorCalidadAntisesgo.mediana_ponderada(valores, pesos)
        media_cruda = round(float(np.mean(valores)), 2) if valores else None
        frecuencias = {
            str(escala): int(sum(1 for v in valores_validos if v == escala))
            for escala in range(1, 6)
        }

        dimensiones_resumen[dim_key] = {
            "mediana_ponderada": mediana_pond,
            "media_cruda_secundaria": media_cruda,
            "n_respuestas_dim": len(valores_validos),
            "frecuencias_1_a_5": frecuencias,
            "valores_boxplot": valores_validos,
        }

    return {
        "curso_codigo": curso_codigo,
        "semestre": semestre,
        "version_instrumento": "v0.2",
        "publicable": True,
        "n_total": n_total,
        "n_validas": n_validas,
        "porcentaje_aislados": porcentaje_aislados,
        "dimensiones": dimensiones_resumen,
    }
