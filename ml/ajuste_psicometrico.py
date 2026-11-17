import numpy as np
import pandas as pd
import statsmodels.formula.api as smf


def calcular_alfa_cronbach(df_items: pd.DataFrame) -> float:
    """Calcula el Alfa de Cronbach para verificar la consistencia interna del bloque."""
    datos = df_items.dropna()
    k = datos.shape[1]
    if k < 2 or len(datos) < 2:
        return 0.0
    varianzas_items = datos.var(axis=0, ddof=1).sum()
    varianza_total = datos.sum(axis=1).var(ddof=1)
    if varianza_total == 0:
        return 0.0
    return float((k / (k - 1.0)) * (1.0 - (varianzas_items / varianza_total)))


def ajustar_modelo_lineal_mixto(df: pd.DataFrame, dimension_col: str = "DIM_01"):
    """
    Etapa C (Escala institucional): Ajusta un modelo lineal mixto con statsmodels
    descontando el interés previo (SEP_01), si la materia es obligatoria (SEP_02),
    la nota esperada (SEP_03) y la asistencia (AR_01), aislando el efecto propio
    de cada docente (intercepto aleatorio por docente_id).
    """
    df_val = df[df[dimension_col] > 0].copy()
    formula = f"{dimension_col} ~ SEP_01 + SEP_02 + SEP_03 + AR_01"
    modelo = smf.mixedlm(formula, df_val, groups=df_val["docente_id"])
    resultado = modelo.fit(reml=True)
    return resultado
