import os
from typing import Dict, List, Optional, Any
import numpy as np
import joblib
from app.schemas.instrumento_v02 import (
    EnvioEncuestaV02,
    FichaHechosCurso,
    ResultadoMotorCalidad,
)

PARES_DIM_INV = [
    ("DIM_01", "INV_01"),
    ("DIM_02", "INV_02"),
    ("DIM_04", "INV_03"),
    ("DIM_05", "INV_04"),
]

ITEMS_ESCALA_0_5 = [
    "DIM_01", "DIM_02", "DIM_03", "DIM_04", "DIM_05", "DIM_06", "DIM_07", "DIM_08",
    "REF_01", "REF_02", "REF_03",
    "INV_01", "INV_02", "INV_03", "INV_04"
]


def _calcular_racha_maxima(valores: List[int]) -> int:
    if not valores:
        return 0
    max_racha = 1
    racha_actual = 1
    for i in range(1, len(valores)):
        if valores[i] == valores[i - 1]:
            racha_actual += 1
            if racha_actual > max_racha:
                max_racha = racha_actual
        else:
            racha_actual = 1
    return max_racha


class MotorCalidadAntisesgo:
    """
    Motor de calidad de respuesta en 3 etapas:
      - Etapa A: Reglas psicométricas explicables (inconsistencia inversa, contradicción
        con hechos del curso, línea recta, rapidez, arrastre por materia y exposición).
      - Etapa B: Clasificador entrenado y calibrado que asigna un peso w entre 0 y 1.
      - Etapa C: Agregación robusta por mediana ponderada (solo si N >= 5).
    """

    def __init__(self, model_path: Optional[str] = None):
        self.model = None
        if model_path and os.path.exists(model_path):
            self.model = joblib.load(model_path)

    def evaluar_etapa_a(
        self, envio: EnvioEncuestaV02, ficha: FichaHechosCurso
    ) -> Dict[str, Any]:
        datos = envio.model_dump()

        # 1. Inconsistencia inversa: d_k = |x_DIM_k + x_INV_k - 6|, omitiendo pares con algún 0 = No aplica
        desviaciones_pares: Dict[str, float] = {}
        bandera_inconsistencia_inversa = False
        for dim_key, inv_key in PARES_DIM_INV:
            x_dim = datos[dim_key]
            x_inv = datos[inv_key]
            if x_dim > 0 and x_inv > 0:
                d_k = float(abs(x_dim + x_inv - 6))
                desviaciones_pares[f"{dim_key}_{inv_key}"] = d_k
                if d_k >= 3.0:
                    bandera_inconsistencia_inversa = True

        desviacion_inversa_media = (
            float(np.mean(list(desviaciones_pares.values())))
            if desviaciones_pares
            else 0.0
        )

        # 2. Contradicción con la ficha de hechos del curso (REF-01, REF-02, REF-03)
        # Bandera si marca 1-2 con hecho cumplido, o 5 con hecho incumplido
        pares_ref = [
            (datos["REF_01"], ficha.ref_01_plazo_cumplido),
            (datos["REF_02"], ficha.ref_02_programa_detallado),
            (datos["REF_03"], ficha.ref_03_asesorias_cumplidas),
        ]
        contradicciones_ref = 0
        for valor_ref, hecho_cumplido in pares_ref:
            if valor_ref == 0:
                continue
            if hecho_cumplido and valor_ref in (1, 2):
                contradicciones_ref += 1
            elif (not hecho_cumplido) and valor_ref == 5:
                contradicciones_ref += 1
        bandera_contradiccion_hechos = contradicciones_ref >= 1

        # 3. Respuesta en línea recta (sobre los 15 ítems de escala 1..5 / 0=NA)
        valores_escala = [datos[k] for k in ITEMS_ESCALA_0_5]
        valores_validos = [v for v in valores_escala if v > 0]
        racha_maxima = _calcular_racha_maxima(valores_validos)
        if valores_validos:
            conteos = np.bincount(valores_validos)
            proporcion_mismo_valor = float(np.max(conteos) / len(valores_validos))
            desviacion_intraindividual = float(np.std(valores_validos))
        else:
            proporcion_mismo_valor = 1.0
            desviacion_intraindividual = 0.0

        bandera_linea_recta = proporcion_mismo_valor >= 0.90
        porcentaje_no_aplica = float(
            sum(1 for v in valores_escala if v == 0) / len(valores_escala)
        )

        # 4. Respuesta demasiado rápida (< 2 s por ítem frente a 21 ítems -> < 42 s)
        bandera_demasiado_rapida = envio.duracion_seg < (21 * 2)

        # 5. Regla específica AR-03 vs DIM-06:
        # Quien nunca usó asesorías (AR-03 == 1) y califica DIM-06 en 1 se marca para revisión
        bandera_revision_asesoria = (envio.AR_03 == 1) and (envio.DIM_06 == 1)

        # 6. Arrastre por la materia (SEP-01 bajo y todas las DIM válidas en 1 aunque REF se cumplan)
        dims_validas = [datos[f"DIM_0{i}"] for i in range(1, 9) if datos[f"DIM_0{i}"] > 0]
        hechos_cumplidos_todos = (
            ficha.ref_01_plazo_cumplido
            and ficha.ref_02_programa_detallado
            and ficha.ref_03_asesorias_cumplidas
        )
        senal_arrastre_materia = (
            envio.SEP_01 <= 2
            and len(dims_validas) > 0
            and all(v == 1 for v in dims_validas)
            and hechos_cumplidos_todos
        )

        # 7. Baja exposición (AR-01 y AR-02 en 0-25% -> valor 1): se analiza como grupo aparte, no se descarta
        grupo_baja_exposicion = (envio.AR_01 == 1) and (envio.AR_02 == 1)

        return {
            "desviacion_inversa_media": round(desviacion_inversa_media, 4),
            "desviaciones_pares": desviaciones_pares,
            "contradicciones_ref": contradicciones_ref,
            "racha_maxima_iguales": racha_maxima,
            "proporcion_mismo_valor": round(proporcion_mismo_valor, 4),
            "desviacion_intraindividual": round(desviacion_intraindividual, 4),
            "porcentaje_no_aplica": round(porcentaje_no_aplica, 4),
            "bandera_inconsistencia_inversa": bandera_inconsistencia_inversa,
            "bandera_contradiccion_hechos": bandera_contradiccion_hechos,
            "bandera_linea_recta": bandera_linea_recta,
            "bandera_demasiado_rapida": bandera_demasiado_rapida,
            "bandera_revision_asesoria": bandera_revision_asesoria,
            "senal_arrastre_materia": senal_arrastre_materia,
            "grupo_baja_exposicion": grupo_baja_exposicion,
        }

    @staticmethod
    def calcular_peso_desde_probabilidad(p: float) -> float:
        """
        Regla de ponderación Etapa B:
          w = 1       si p < 0.3
          w = 1 - p   si 0.3 <= p <= 0.7
          w = 0       si p > 0.7 (aislado)
        """
        if p < 0.3:
            return 1.0
        elif p <= 0.7:
            return round(1.0 - p, 4)
        else:
            return 0.0

    def evaluar_envio(
        self, envio: EnvioEncuestaV02, ficha: FichaHechosCurso
    ) -> ResultadoMotorCalidad:
        senales = self.evaluar_etapa_a(envio, ficha)

        if self.model is not None:
            vector_features = np.array([[
                senales["desviacion_inversa_media"],
                float(senales["bandera_inconsistencia_inversa"]),
                float(senales["bandera_contradiccion_hechos"]),
                float(senales["contradicciones_ref"]),
                float(senales["bandera_linea_recta"]),
                senales["racha_maxima_iguales"],
                senales["proporcion_mismo_valor"],
                senales["desviacion_intraindividual"],
                senales["porcentaje_no_aplica"],
                float(senales["bandera_demasiado_rapida"]),
                float(envio.duracion_seg),
                float(senales["bandera_revision_asesoria"]),
                float(senales["senal_arrastre_materia"]),
                float(envio.AR_01),
                float(envio.AR_02),
                float(envio.AR_03),
                float(envio.SEP_01),
                float(envio.SEP_02),
                float(envio.SEP_03),
            ]])
            prob_inconsistente = float(self.model.predict_proba(vector_features)[0, 1])
        else:
            # Heurística explicable de respaldo cuando aún no se carga el archivo .joblib
            score = 0.0
            if senales["bandera_inconsistencia_inversa"]:
                score += 0.35
            if senales["bandera_contradiccion_hechos"]:
                score += 0.25
            if senales["bandera_linea_recta"]:
                score += 0.30
            if senales["bandera_demasiado_rapida"]:
                score += 0.25
            if senales["senal_arrastre_materia"]:
                score += 0.15
            if senales["bandera_revision_asesoria"]:
                score += 0.15
            prob_inconsistente = min(0.99, score)

        prob_inconsistente = round(prob_inconsistente, 4)
        peso = self.calcular_peso_desde_probabilidad(prob_inconsistente)

        return ResultadoMotorCalidad(
            desviacion_inversa_media=senales["desviacion_inversa_media"],
            desviaciones_pares=senales["desviaciones_pares"],
            racha_maxima_iguales=senales["racha_maxima_iguales"],
            proporcion_mismo_valor=senales["proporcion_mismo_valor"],
            desviacion_intraindividual=senales["desviacion_intraindividual"],
            porcentaje_no_aplica=senales["porcentaje_no_aplica"],
            bandera_inconsistencia_inversa=senales["bandera_inconsistencia_inversa"],
            bandera_contradiccion_hechos=senales["bandera_contradiccion_hechos"],
            bandera_linea_recta=senales["bandera_linea_recta"],
            bandera_demasiado_rapida=senales["bandera_demasiado_rapida"],
            bandera_revision_asesoria=senales["bandera_revision_asesoria"],
            senal_arrastre_materia=senales["senal_arrastre_materia"],
            grupo_baja_exposicion=senales["grupo_baja_exposicion"],
            prob_inconsistente=prob_inconsistente,
            peso_calidad=peso,
            aislado=(peso == 0.0),
        )

    @staticmethod
    def mediana_ponderada(valores: List[float], pesos: List[float]) -> Optional[float]:
        """Calcula la mediana ponderada por w excluyendo pesos nulos."""
        pares = [(v, w) for v, w in zip(valores, pesos) if v > 0 and w > 0]
        if not pares:
            return None
        pares.sort(key=lambda x: x[0])
        vals = np.array([p[0] for p in pares], dtype=float)
        ws = np.array([p[1] for p in pares], dtype=float)
        cum_weights = np.cumsum(ws)
        mitad = 0.5 * np.sum(ws)
        idx = int(np.searchsorted(cum_weights, mitad))
        return float(vals[min(idx, len(vals) - 1)])
