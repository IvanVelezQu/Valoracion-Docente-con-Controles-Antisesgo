from typing import Dict, List, Any
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr
import numpy as np

from app.core.config import settings
from app.schemas.instrumento_v02 import (
    EnvioEncuestaV02,
    FichaHechosCurso,
    ORDEN_PRESENTACION_V02,
)
from app.services.motor_calidad import MotorCalidadAntisesgo
from app.services.firma_ciega import GestorFirmaCiegaSimulado

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

motor_calidad = MotorCalidadAntisesgo(model_path=settings.MODEL_PATH)
gestor_firma = GestorFirmaCiegaSimulado()

# Almacenamiento en memoria para entorno de desarrollo local (simula las 2 BD separadas)
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
    correo_institucional: EmailStr
    curso_codigo: str
    semestre: str = "2026-2"
    token_cegado: str


@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "instrumento": "v0.2",
        "total_items": len(ORDEN_PRESENTACION_V02),
        "orden_presentacion": ORDEN_PRESENTACION_V02,
        "modelo_cargado": motor_calidad.model is not None,
    }


@app.post("/api/v1/auth/solicitar-token-ciego")
def solicitar_token_ciego(req: SolicitudTokenCiego):
    """
    Paso 1 y 2: Valida correo @udea.edu.co en la BD de Control y emite firma ciega
    sin asociar el token a las respuestas futuras.
    """
    dominio = req.correo_institucional.split("@")[-1].lower()
    if dominio != settings.ALLOWED_EMAIL_DOMAIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Solo se permiten cuentas institucionales @{settings.ALLOWED_EMAIL_DOMAIN}",
        )

    llave_matricula = gestor_firma.hash_identificador(
        f"{req.correo_institucional}:{req.curso_codigo}:{req.semestre}"
    )
    if llave_matricula in BD_CONTROL_EMISIONES:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="El estudiante ya solicitó un token anónimo para este curso.",
        )

    firma_ciega = gestor_firma.emitir_firma_ciega(req.token_cegado)
    BD_CONTROL_EMISIONES.add(llave_matricula)
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

    # Consumo atómico del token (BD de control) y registro anónimo (BD de respuestas)
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
    envios_curso = [
        r for r in BD_RESPUESTAS_ENVIOS
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
