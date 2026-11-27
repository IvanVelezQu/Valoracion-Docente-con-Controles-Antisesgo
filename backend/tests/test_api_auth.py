import pytest
from fastapi import HTTPException
from fastapi.routing import APIRoute
from pydantic import ValidationError

from app.main import (
    BD_CONTROL_EMISIONES,
    SolicitudTokenCiego,
    app,
    health_check,
    solicitar_token_ciego,
)
from app.services.auth_supabase import verificar_usuario_udea


def _run_sync_coro(coro):
    """Ejecuta corrutinas sin I/O pendiente sin requerir socketpair del loop."""
    try:
        coro.send(None)
    except StopIteration as stop:
        return stop.value
    finally:
        coro.close()


def test_health_reporta_modelo_cargado():
    body = health_check()
    assert body["status"] == "ok"
    assert body["instrumento"] == "v0.2"
    assert body["total_items"] == 21
    assert body["modelo_cargado"] is True


def test_endpoint_token_ciego_esta_protegido_con_verificar_usuario_udea():
    rutas = [
        r for r in app.routes
        if isinstance(r, APIRoute) and r.path == "/api/v1/auth/solicitar-token-ciego"
    ]
    assert len(rutas) == 1
    deps = [d.call for d in rutas[0].dependant.dependencies]
    assert verificar_usuario_udea in deps


def test_verificar_usuario_udea_rechaza_header_sin_bearer():
    with pytest.raises(HTTPException) as exc:
        _run_sync_coro(verificar_usuario_udea(authorization="Basic invalid"))
    assert exc.value.status_code == 401


def test_solicitar_token_emite_firma_ciega_y_evita_duplicado():
    BD_CONTROL_EMISIONES.clear()
    try:
        req = SolicitudTokenCiego(
            correo_institucional="estudiante.prueba@udea.edu.co",
            curso_codigo="ING-SIS-2026",
            semestre="2026-2",
            token_cegado="token_anonimo_udea_v02_654321",
        )
        res_ok = _run_sync_coro(
            solicitar_token_ciego(req=req, correo_verificado="estudiante.prueba@udea.edu.co")
        )
        assert res_ok["curso_codigo"] == "ING-SIS-2026"
        assert len(res_ok["firma_ciega"]) >= 16

        with pytest.raises(HTTPException) as exc_dup:
            _run_sync_coro(
                solicitar_token_ciego(req=req, correo_verificado="estudiante.prueba@udea.edu.co")
            )
        assert exc_dup.value.status_code == 409
    finally:
        BD_CONTROL_EMISIONES.clear()


def test_solicitar_token_rechaza_correo_distinto_al_jwt_y_token_corto():
    req = SolicitudTokenCiego(
        correo_institucional="otro.usuario@udea.edu.co",
        curso_codigo="ING-SIS-2026",
        semestre="2026-2",
        token_cegado="token_anonimo_udea_v02_999999",
    )
    with pytest.raises(HTTPException) as exc:
        _run_sync_coro(
            solicitar_token_ciego(req=req, correo_verificado="estudiante.real@udea.edu.co")
        )
    assert exc.value.status_code == 403

    with pytest.raises(ValidationError):
        SolicitudTokenCiego(
            curso_codigo="ING-SIS-2026",
            semestre="2026-2",
            token_cegado="corto_123",
        )
