from app.schemas.instrumento_v02 import EnvioEncuestaV02, FichaHechosCurso
from app.services.motor_calidad import MotorCalidadAntisesgo


def crear_ficha_base() -> FichaHechosCurso:
    return FichaHechosCurso(
        curso_codigo="ING-SIS-2026",
        semestre="2026-2",
        ref_01_plazo_cumplido=True,
        ref_02_programa_detallado=True,
        ref_03_asesorias_cumplidas=True,
        dias_promedio_calificacion=5.0,
    )


def test_estudiante_honesto_recibe_peso_1():
    motor = MotorCalidadAntisesgo()
    ficha = crear_ficha_base()
    # Par inverso coherente: DIM=5 e INV=1 -> suma = 6 (d_k = 0)
    envio = EnvioEncuestaV02(
        curso_codigo="ING-SIS-2026",
        token_anonimo="token_valido_1234567890",
        firma_token="firma_valida_1234567890",
        duracion_seg=210,
        AR_01=4, AR_02=4, AR_03=3,
        SEP_01=4, SEP_02=1, SEP_03=4,
        DIM_01=5, DIM_02=4, DIM_03=5, DIM_04=4,
        DIM_05=5, DIM_06=4, DIM_07=5, DIM_08=4,
        REF_01=5, REF_02=5, REF_03=4,
        INV_01=1, INV_02=2, INV_03=2, INV_04=1,
    )
    res = motor.evaluar_envio(envio, ficha)
    assert res.desviacion_inversa_media == 0.0
    assert not res.bandera_inconsistencia_inversa
    assert not res.bandera_contradiccion_hechos
    assert not res.bandera_linea_recta
    assert not res.bandera_demasiado_rapida
    assert res.peso_calidad == 1.0
    assert not res.aislado


def test_efecto_halo_todo_5_y_rapido_se_aisla():
    motor = MotorCalidadAntisesgo()
    ficha = crear_ficha_base()
    # Marca 5 en DIM y también 5 en INV (suma=10, d_k=4 >= 3) en 20 segundos
    envio = EnvioEncuestaV02(
        curso_codigo="ING-SIS-2026",
        token_anonimo="token_halo_1234567890",
        firma_token="firma_halo_1234567890",
        duracion_seg=20,
        AR_01=4, AR_02=4, AR_03=2,
        SEP_01=5, SEP_02=1, SEP_03=5,
        DIM_01=5, DIM_02=5, DIM_03=5, DIM_04=5,
        DIM_05=5, DIM_06=5, DIM_07=5, DIM_08=5,
        REF_01=5, REF_02=5, REF_03=5,
        INV_01=5, INV_02=5, INV_03=5, INV_04=5,
    )
    res = motor.evaluar_envio(envio, ficha)
    assert res.bandera_inconsistencia_inversa
    assert res.bandera_linea_recta
    assert res.bandera_demasiado_rapida
    assert res.aislado
    assert res.peso_calidad == 0.0
