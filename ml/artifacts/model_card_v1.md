# Tarjeta del Modelo — `modelo_calidad_v1.joblib`

## Propósito y alcance
Clasificador calibrado de la **Etapa B** del Motor de Calidad de Respuesta para el Instrumento v0.2 de Valoración Docente. Estima la probabilidad $p$ de que un envío presente patrones de respuesta inconsistentes (descuido, efecto halo, represalia/horn o arrastre por rechazo a la materia) sin utilizar la distancia a la opinión del grupo ni datos demográficos.

## Datos de entrenamiento
- **Origen**: Generador sintético (`ml/generador_sintetico.py`) con 20.000 encuestas sobre 60 docentes ficticios.
- **Partición**: 70% entrenamiento (14.000), 15% validación (3.000), 15% prueba (3.000), estratificada por perfil (`honesto` 65%, `descuidado` 10%, `halo` 7%, `horn_represalia` 10%, `rechazo_materia` 8%).

## Métricas en el conjunto de prueba (15%)
- **F1-Score (Regresión Logística base - Validación)**: 0.9957
- **F1-Score (HistGradientBoosting Calibrado - Prueba)**: 1.0000
- **Brier Score Loss (Calibración de probabilidades)**: 0.0000

## Variables con mayor importancia por permutación
- **`duracion_seg`**: 0.2673
- **`SEP_01`**: 0.1667
- **`desviacion_inversa_media`**: 0.0454
- **`bandera_inconsistencia_inversa`**: 0.0000
- **`bandera_contradiccion_hechos`**: 0.0000
- **`contradicciones_ref`**: 0.0000
- **`bandera_linea_recta`**: 0.0000
- **`racha_maxima_iguales`**: 0.0000

## Regla de ponderación aplicada en la API
- $p < 0.30 \implies w = 1.0$ (peso completo)
- $0.30 \le p \le 0.70 \implies w = 1 - p$ (ponderación gradual)
- $p > 0.70 \implies w = 0.0$ (envío aislado del agregado; nunca sanciona ni identifica al estudiante)
