# Módulo de Valoración Docente con Controles Antisesgo (Instrumento v0.2)

Repositorio base para el **Proyecto Integrador I (2026-2) · Grupo 5**. Implementa una arquitectura desacoplada de costo `$0` en licencias donde la identidad del estudiante y sus respuestas nunca comparten base de datos, sumando un **Motor de Calidad de Respuesta en 3 etapas** (reglas psicométricas explicables, clasificador calibrado entrenado con datos sintéticos y ajuste estadístico por mediana ponderada).

## Estructura del proyecto

```text
valoracion-docente-antisesgo/
├── .env.example                        # Variables de entorno para Supabase, Neon y FastAPI
├── .github/workflows/
│   └── recalculo_nocturno.yml          # GitHub Action programada para recálculo nocturno
├── db/
│   ├── schema_control_supabase.sql     # Esquema BD de Control (Supabase: matrícula y tokens)
│   └── schema_respuestas_neon.sql      # Esquema BD de Respuestas (Neon: v0.2, fichas y pesos)
├── backend/
│   ├── requirements.txt                # Dependencias de Python (FastAPI, scikit-learn, statsmodels)
│   ├── app/
│   │   ├── core/config.py              # Configuración general y reglas (N >= 5, @udea.edu.co)
│   │   ├── schemas/instrumento_v02.py  # Validación estricta 0-5 y orden de los 21 ítems
│   │   ├── services/firma_ciega.py     # Emisión y verificación de tokens desacoplados
│   │   ├── services/motor_calidad.py   # Etapas A, B y C del motor antisesgo
│   │   └── main.py                     # Endpoints FastAPI (auth, envío atómico y dashboard)
│   └── tests/
│       └── test_motor_calidad.py       # Pruebas unitarias con pytest
├── ml/
│   ├── generador_sintetico.py          # Generador de 20.000 encuestas (5 perfiles sobre 60 docentes)
│   ├── entrenar_modelo.py              # Entrenamiento 70/15/15 (LR + HistGradientBoosting calibrado)
│   ├── ajuste_psicometrico.py          # Alfa de Cronbach y Modelo Lineal Mixto (statsmodels)
│   └── artifacts/
│       ├── modelo_calidad_v1.joblib    # Clasificador calibrado preentrenado listo para FastAPI
│       ├── model_card_v1.md            # Tarjeta del modelo con métricas e importancia de variables
│       └── muestra_sintetica_v02.csv   # Muestra de 500 encuestas sintéticas etiquetadas
└── frontend/
    ├── package.json                    # Configuración React + Vite + TypeScript + Tailwind + Plotly
    └── src/
        ├── types/instrumento.ts        # Los 21 ítems en el orden exacto de presentación
        ├── components/FormularioEncuesta.tsx  # Interfaz del estudiante (escala 0-5 y duración)
        └── components/DashboardDocente.tsx    # Boxplots, frecuencias y bloqueo N < 5
```

## Inicio rápido

### 1. Backend (FastAPI) y Pruebas
```bash
cd backend
pip install -r requirements.txt
PYTHONPATH=. pytest tests/
uvicorn app.main:app --reload --port 8000
```

### 2. Reentrenamiento del Modelo Fuera de Línea (Colab / Local)
```bash
cd ml
python entrenar_modelo.py
```

### 3. Frontend (React + Vite + TypeScript)
```bash
cd frontend
npm install
npm run dev
```
