import hashlib
import hmac
import secrets
from typing import Tuple

class GestorFirmaCiegaSimulado:
    """
    Adaptador de firma ciega (RFC 9474 / blind-rsa-signatures) para desacoplar
    la identidad del estudiante (@udea.edu.co) del envío de la encuesta.
    En producción se enlaza con la llave RSA privada del servidor sin almacenar
    jamás el token en texto claro en la BD de control.
    """

    def __init__(self, secret_key: str = "udea-blind-rsa-dev-secret-2026"):
        self._secret_key = secret_key.encode("utf-8")

    def emitir_firma_ciega(self, token_cegado_hex: str) -> str:
        """Firma el mensaje cegado sin conocer el token subyacente."""
        return hmac.new(
            self._secret_key, token_cegado_hex.encode("utf-8"), hashlib.sha256
        ).hexdigest()

    def verificar_token_anonimo(self, token_anonimo: str, firma_token: str) -> bool:
        """Verifica que el token presentado con la encuesta fue firmado válidamente."""
        esperada = hmac.new(
            self._secret_key, token_anonimo.encode("utf-8"), hashlib.sha256
        ).hexdigest()
        return hmac.compare_digest(esperada, firma_token)

    @staticmethod
    def hash_identificador(valor: str) -> str:
        return hashlib.sha256(valor.strip().lower().encode("utf-8")).hexdigest()
