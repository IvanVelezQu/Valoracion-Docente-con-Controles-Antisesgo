import os
import joblib
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import HistGradientBoostingClassifier, IsolationForest
from sklearn.calibration import CalibratedClassifierCV
from sklearn.inspection import permutation_importance
from sklearn.metrics import f1_score, brier_score_loss, classification_report

from generador_sintetico import generar_encuestas_sinteticas

FEATURE_COLS = [
    "desviacion_inversa_media",
    "bandera_inconsistencia_inversa",
    "bandera_contradiccion_hechos",
    "contradicciones_ref",
    "bandera_linea_recta",
    "racha_maxima_iguales",
    "proporcion_mismo_valor",
    "desviacion_intraindividual",
    "porcentaje_no_aplica",
    "bandera_demasiado_rapida",
    "duracion_seg",
    "bandera_revision_asesoria",
    "senal_arrastre_materia",
    "AR_01",
    "AR_02",
    "AR_03",
    "SEP_01",
    "SEP_02",
    "SEP_03",
]


def entrenar_y_exportar(output_dir: str = "artifacts"):
    os.makedirs(output_dir, exist_ok=True)
    df = generar_encuestas_sinteticas(n_encuestas=20000, n_docentes=60, seed=42)

    # Guardar muestra de 500 filas para inspección rápida y pruebas locales
    df.head(500).to_csv(os.path.join(output_dir, "muestra_sintetica_v02.csv"), index=False)

    X = df[FEATURE_COLS].values
    y = df["es_inconsistente"].values
    perfiles = df["perfil"].values

    # División 70 / 15 / 15 estratificada por perfil
    X_train, X_temp, y_train, y_temp, p_train, p_temp = train_test_split(
        X, y, perfiles, test_size=0.30, random_state=42, stratify=perfiles
    )
    X_val, X_test, y_val, y_test, p_val, p_test = train_test_split(
        X_temp, y_temp, p_temp, test_size=0.50, random_state=42, stratify=p_temp
    )

    # 1. Línea base explicable: Regresión Logística
    lr_base = LogisticRegression(max_iter=1000, random_state=42)
    lr_base.fit(X_train, y_train)
    f1_lr = f1_score(y_val, lr_base.predict(X_val))

    # 2. Clasificador principal: HistGradientBoostingClassifier calibrado
    hgb = HistGradientBoostingClassifier(max_depth=5, learning_rate=0.08, random_state=42)
    modelo_calibrado = CalibratedClassifierCV(estimator=hgb, method="isotonic", cv=3)
    modelo_calibrado.fit(X_train, y_train)

    y_pred_test = modelo_calibrado.predict(X_test)
    y_prob_test = modelo_calibrado.predict_proba(X_test)[:, 1]
    f1_test = f1_score(y_test, y_pred_test)
    brier_test = brier_score_loss(y_test, y_prob_test)

    # 3. Importancia de variables por permutación
    perm = permutation_importance(
        modelo_calibrado, X_test, y_test, n_repeats=5, random_state=42
    )
    importancias = sorted(
        zip(FEATURE_COLS, perm.importances_mean), key=lambda x: x[1], reverse=True
    )

    # Exportar modelo versión v1
    ruta_modelo = os.path.join(output_dir, "modelo_calidad_v1.joblib")
    joblib.dump(modelo_calibrado, ruta_modelo)

    # Generar Tarjeta del Modelo (Model Card)
    top_vars_md = "\n".join(
        [f"- **`{nombre}`**: {imp:.4f}" for nombre, imp in importancias[:8]]
    )
    model_card = f"""# Tarjeta del Modelo — `modelo_calidad_v1.joblib`

## Propósito y alcance
Clasificador calibrado de la **Etapa B** del Motor de Calidad de Respuesta para el Instrumento v0.2 de Valoración Docente. Estima la probabilidad $p$ de que un envío presente patrones de respuesta inconsistentes (descuido, efecto halo, represalia/horn o arrastre por rechazo a la materia) sin utilizar la distancia a la opinión del grupo ni datos demográficos.

## Datos de entrenamiento
- **Origen**: Generador sintético (`ml/generador_sintetico.py`) con 20.000 encuestas sobre 60 docentes ficticios.
- **Partición**: 70% entrenamiento (14.000), 15% validación (3.000), 15% prueba (3.000), estratificada por perfil (`honesto` 65%, `descuidado` 10%, `halo` 7%, `horn_represalia` 10%, `rechazo_materia` 8%).

## Métricas en el conjunto de prueba (15%)
- **F1-Score (Regresión Logística base - Validación)**: {f1_lr:.4f}
- **F1-Score (HistGradientBoosting Calibrado - Prueba)**: {f1_test:.4f}
- **Brier Score Loss (Calibración de probabilidades)**: {brier_test:.4f}

## Variables con mayor importancia por permutación
{top_vars_md}

## Regla de ponderación aplicada en la API
- $p < 0.30 \implies w = 1.0$ (peso completo)
- $0.30 \le p \le 0.70 \implies w = 1 - p$ (ponderación gradual)
- $p > 0.70 \implies w = 0.0$ (envío aislado del agregado; nunca sanciona ni identifica al estudiante)
"""
    with open(os.path.join(output_dir, "model_card_v1.md"), "w", encoding="utf-8") as f:
        f.write(model_card)

    return f1_lr, f1_test, brier_test


if __name__ == "__main__":
    f1_lr, f1_test, brier = entrenar_y_exportar("artifacts")
    print(f"Entrenamiento completado -> F1 LR: {f1_lr:.4f} | F1 HGB Calibrado: {f1_test:.4f} | Brier: {brier:.4f}")
