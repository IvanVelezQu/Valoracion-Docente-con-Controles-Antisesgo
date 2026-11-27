import os
import httpx
from fastapi import Header, HTTPException, status

from app.core.config import settings

DOMINIO_PERMITIDO = f"@{settings.ALLOWED_EMAIL_DOMAIN}"


async def verificar_usuario_udea(authorization: str = Header(...)) -> str:
    """
    Valida el JWT emitido por Supabase Auth (Google) y retorna el correo @udea.edu.co.
    """
    if not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Falta el encabezado Authorization con formato Bearer.",
        )

    token = authorization.replace("Bearer ", "", 1).strip()
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="El token Bearer está vacío.",
        )

    supabase_url = (os.getenv("SUPABASE_URL") or settings.SUPABASE_URL or "").strip().rstrip("/")
    supabase_anon_key = (os.getenv("SUPABASE_ANON_KEY") or settings.SUPABASE_ANON_KEY or "").strip()

    if not supabase_url or not supabase_anon_key:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Faltan SUPABASE_URL o SUPABASE_ANON_KEY en el servidor.",
        )

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            res = await client.get(
                f"{supabase_url}/auth/v1/user",
                headers={
                    "Authorization": f"Bearer {token}",
                    "apikey": supabase_anon_key,
                },
            )
    except httpx.RequestError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="No se pudo validar la sesión contra Supabase Auth.",
        )

    if res.status_code != 200:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Sesión de Google/Supabase inválida o expirada.",
        )

    correo = (res.json().get("email") or "").strip().lower()
    if not correo.endswith(DOMINIO_PERMITIDO):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Acceso restringido a correos institucionales {DOMINIO_PERMITIDO}.",
        )

    return correo
