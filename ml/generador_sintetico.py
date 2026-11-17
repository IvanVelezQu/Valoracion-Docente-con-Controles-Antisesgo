import numpy as np
import pandas as pd

PERFILES_PROPORCIONES = {
    "honesto": 0.65,
    "descuidado": 0.10,
    "halo": 0.07,
    "horn_represalia": 0.10,
    "rechazo_materia": 0.08,
}


def _calcular_racha_max(vals):
    if not vals:
        return 0
    max_r = 1
    cur = 1
    for i in range(1, len(vals)):
        if vals[i] == vals[i - 1]:
            cur += 1
            if cur > max_r:
                max_r = cur
        else:
            cur = 1
    return max_r


def generar_encuestas_sinteticas(
    n_encuestas: int = 20000, n_docentes: int = 60, seed: int = 42
) -> pd.DataFrame:
    """
    Simula 20.000 encuestas sobre 60 docentes ficticios con los 5 perfiles definidos:
      - Honesto (65%): Calidad real del docente + ruido pequeño; inversos coherentes; REF acordes.
      - Descuidado (10%): Valores aleatorios, tiempo de respuesta corto.
      - Halo (7%): 5 en DIM e INV por igual; REF en 5 aunque el hecho no se cumpla.
      - Horn / represalia (10%): 1 en todo, más marcado en DIM-04 y DIM-08; nota esperada baja; REF contradice.
      - Rechazo a la materia (8%): Interés previo bajo arrastra todas las DIM; inversos coherentes.
    """
    rng = np.random.default_rng(seed)

    # Generar fichas y calidad real para los 60 docentes ficticios
    docentes = {}
    for d_id in range(1, n_docentes + 1):
        calidad_base = rng.uniform(2.5, 4.8)
        docentes[d_id] = {
            "calidad_dim": np.clip(rng.normal(calidad_base, 0.35, size=8), 1.5, 5.0),
            "ref_01_cumplido": bool(rng.random() < 0.80),
            "ref_02_cumplido": bool(rng.random() < 0.85),
            "ref_03_cumplido": bool(rng.random() < 0.78),
        }

    perfiles_nombres = list(PERFILES_PROPORCIONES.keys())
    perfiles_probs = list(PERFILES_PROPORCIONES.values())
    perfiles_asignados = rng.choice(perfiles_nombres, size=n_encuestas, p=perfiles_probs)

    registros = []
    for idx in range(n_encuestas):
        perfil = perfiles_asignados[idx]
        doc_id = int(rng.integers(1, n_docentes + 1))
        doc = docentes[doc_id]

        if perfil == "honesto":
            duracion_seg = int(rng.normal(230, 45))
            ar_01 = int(rng.choice([2, 3, 4], p=[0.1, 0.3, 0.6]))
            ar_02 = int(rng.choice([2, 3, 4], p=[0.15, 0.45, 0.4]))
            ar_03 = int(rng.choice([1, 2, 3, 4], p=[0.2, 0.4, 0.25, 0.15]))
            sep_01 = int(rng.choice([2, 3, 4, 5], p=[0.1, 0.3, 0.4, 0.2]))
            sep_02 = int(rng.choice([0, 1], p=[0.25, 0.75]))
            sep_03 = int(rng.choice([3, 4, 5], p=[0.25, 0.5, 0.25]))

            dims = [
                int(np.clip(np.round(doc["calidad_dim"][i] + rng.normal(0, 0.45)), 1, 5))
                for i in range(8)
            ]
            # Inversos coherentes: suma con DIM_01, DIM_02, DIM_04, DIM_05 ≈ 6
            invs = [
                int(np.clip(6 - dims[0] + rng.choice([-1, 0, 1], p=[0.15, 0.7, 0.15]), 1, 5)),
                int(np.clip(6 - dims[1] + rng.choice([-1, 0, 1], p=[0.15, 0.7, 0.15]), 1, 5)),
                int(np.clip(6 - dims[3] + rng.choice([-1, 0, 1], p=[0.15, 0.7, 0.15]), 1, 5)),
                int(np.clip(6 - dims[4] + rng.choice([-1, 0, 1], p=[0.15, 0.7, 0.15]), 1, 5)),
            ]
            refs = [
                int(rng.choice([4, 5], p=[0.3, 0.7])) if doc["ref_01_cumplido"] else int(rng.choice([1, 2, 3], p=[0.4, 0.4, 0.2])),
                int(rng.choice([4, 5], p=[0.25, 0.75])) if doc["ref_02_cumplido"] else int(rng.choice([1, 2, 3], p=[0.4, 0.4, 0.2])),
                int(rng.choice([4, 5], p=[0.3, 0.7])) if doc["ref_03_cumplido"] else int(rng.choice([1, 2, 3], p=[0.4, 0.4, 0.2])),
            ]
            es_inconsistente = 0

        elif perfil == "descuidado":
            duracion_seg = int(rng.integers(12, 48))
            ar_01 = int(rng.integers(1, 5))
            ar_02 = int(rng.integers(1, 5))
            ar_03 = int(rng.integers(1, 5))
            sep_01 = int(rng.integers(1, 6))
            sep_02 = int(rng.integers(0, 2))
            sep_03 = int(rng.integers(1, 6))
            dims = [int(rng.integers(1, 6)) for _ in range(8)]
            invs = [int(rng.integers(1, 6)) for _ in range(4)]
            refs = [int(rng.integers(1, 6)) for _ in range(3)]
            es_inconsistente = 1

        elif perfil == "halo":
            duracion_seg = int(rng.integers(20, 75))
            ar_01 = int(rng.choice([3, 4]))
            ar_02 = int(rng.choice([3, 4]))
            ar_03 = int(rng.choice([2, 3, 4]))
            sep_01 = 5
            sep_02 = int(rng.integers(0, 2))
            sep_03 = 5
            dims = [5] * 8
            invs = [int(rng.choice([4, 5], p=[0.15, 0.85])) for _ in range(4)]
            refs = [5, 5, 5]
            es_inconsistente = 1

        elif perfil == "horn_represalia":
            duracion_seg = int(rng.integers(25, 95))
            ar_01 = int(rng.choice([1, 2, 3], p=[0.4, 0.4, 0.2]))
            ar_02 = int(rng.choice([1, 2], p=[0.5, 0.5]))
            ar_03 = 1
            sep_01 = int(rng.choice([1, 2]))
            sep_02 = 1
            sep_03 = int(rng.choice([1, 2], p=[0.7, 0.3]))
            dims = [int(rng.choice([1, 2], p=[0.85, 0.15])) for _ in range(8)]
            dims[3] = 1  # DIM-04 más marcado
            dims[7] = 1  # DIM-08 más marcado
            invs = [int(rng.choice([1, 2, 5], p=[0.6, 0.2, 0.2])) for _ in range(4)]
            refs = [1, 1, 1]  # Contradice la ficha aunque el docente haya cumplido
            es_inconsistente = 1

        else:  # rechazo_materia
            duracion_seg = int(rng.normal(190, 40))
            ar_01 = int(rng.choice([2, 3, 4], p=[0.3, 0.4, 0.3]))
            ar_02 = int(rng.choice([1, 2, 3], p=[0.3, 0.4, 0.3]))
            ar_03 = int(rng.choice([1, 2], p=[0.6, 0.4]))
            sep_01 = 1  # Interés previo muy bajo
            sep_02 = 1  # Obligatoria
            sep_03 = int(rng.choice([2, 3, 4]))
            dims = [int(rng.choice([1, 2], p=[0.75, 0.25])) for _ in range(8)]
            # Inversos coherentes con su baja calificación (suma ≈ 6)
            invs = [
                int(np.clip(6 - dims[0], 4, 5)),
                int(np.clip(6 - dims[1], 4, 5)),
                int(np.clip(6 - dims[3], 4, 5)),
                int(np.clip(6 - dims[4], 4, 5)),
            ]
            refs = [
                4 if doc["ref_01_cumplido"] else 2,
                4 if doc["ref_02_cumplido"] else 2,
                4 if doc["ref_03_cumplido"] else 2,
            ]
            es_inconsistente = 1

        duracion_seg = max(10, duracion_seg)

        # Calcular señales de Etapa A para el registro
        pares_d = [
            abs(dims[0] + invs[0] - 6),
            abs(dims[1] + invs[1] - 6),
            abs(dims[3] + invs[2] - 6),
            abs(dims[4] + invs[3] - 6),
        ]
        desviacion_inversa_media = float(np.mean(pares_d))
        bandera_inconsistencia_inversa = int(any(d >= 3 for d in pares_d))

        contradicciones_ref = 0
        for val_ref, cumplido in zip(
            refs, [doc["ref_01_cumplido"], doc["ref_02_cumplido"], doc["ref_03_cumplido"]]
        ):
            if cumplido and val_ref in (1, 2):
                contradicciones_ref += 1
            elif (not cumplido) and val_ref == 5:
                contradicciones_ref += 1
        bandera_contradiccion_hechos = int(contradicciones_ref >= 1)

        escala_15 = dims + refs + invs
        racha_max = _calcular_racha_max(escala_15)
        prop_mismo = float(np.max(np.bincount(escala_15)) / len(escala_15))
        std_intra = float(np.std(escala_15))
        bandera_linea_recta = int(prop_mismo >= 0.90)
        porcentaje_no_aplica = 0.0
        bandera_demasiado_rapida = int(duracion_seg < 42)
        bandera_revision_asesoria = int(ar_03 == 1 and dims[5] == 1)
        hechos_todos = doc["ref_01_cumplido"] and doc["ref_02_cumplido"] and doc["ref_03_cumplido"]
        senal_arrastre_materia = int(sep_01 <= 2 and all(d == 1 for d in dims) and hechos_todos)

        registros.append({
            "docente_id": doc_id,
            "perfil": perfil,
            "es_inconsistente": es_inconsistente,
            "duracion_seg": duracion_seg,
            "AR_01": ar_01, "AR_02": ar_02, "AR_03": ar_03,
            "SEP_01": sep_01, "SEP_02": sep_02, "SEP_03": sep_03,
            "DIM_01": dims[0], "DIM_02": dims[1], "DIM_03": dims[2], "DIM_04": dims[3],
            "DIM_05": dims[4], "DIM_06": dims[5], "DIM_07": dims[6], "DIM_08": dims[7],
            "REF_01": refs[0], "REF_02": refs[1], "REF_03": refs[2],
            "INV_01": invs[0], "INV_02": invs[1], "INV_03": invs[2], "INV_04": invs[3],
            "desviacion_inversa_media": desviacion_inversa_media,
            "bandera_inconsistencia_inversa": bandera_inconsistencia_inversa,
            "bandera_contradiccion_hechos": bandera_contradiccion_hechos,
            "contradicciones_ref": contradicciones_ref,
            "bandera_linea_recta": bandera_linea_recta,
            "racha_maxima_iguales": racha_max,
            "proporcion_mismo_valor": prop_mismo,
            "desviacion_intraindividual": std_intra,
            "porcentaje_no_aplica": porcentaje_no_aplica,
            "bandera_demasiado_rapida": bandera_demasiado_rapida,
            "bandera_revision_asesoria": bandera_revision_asesoria,
            "senal_arrastre_materia": senal_arrastre_materia,
        })

    return pd.DataFrame(registros)


if __name__ == "__main__":
    df = generar_encuestas_sinteticas(20000, 60)
    print("Dataset sintético generado:", df.shape)
    print(df["perfil"].value_counts(normalize=True).round(3))
