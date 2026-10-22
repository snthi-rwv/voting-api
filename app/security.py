import hmac
from datetime import datetime, timedelta, timezone
from typing import Optional

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

from app.config import settings

# Le dice a Swagger dónde está el login (activa el botón "Authorize")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def authenticate_admin(username: str, password: str) -> bool:
    # compare_digest compara en tiempo constante, para no filtrar información por tiempos de respuesta
    user_ok = hmac.compare_digest(username.encode(), settings.admin_username.encode())
    pass_ok = hmac.compare_digest(password.encode(), settings.admin_password.encode())
    return user_ok and pass_ok


def create_access_token(subject: str, expires_minutes: Optional[int] = None) -> str:
    minutes = settings.access_token_expire_minutes if expires_minutes is None else expires_minutes
    now = datetime.now(timezone.utc)
    payload = {"sub": subject, "iat": now, "exp": now + timedelta(minutes=minutes)}
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def get_current_user(token: str = Depends(oauth2_scheme)) -> str:
    """Dependencia que protege un endpoint: exige un token JWT válido."""
    error = HTTPException(
        status.HTTP_401_UNAUTHORIZED,
        "Token inválido o expirado",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
    except jwt.InvalidTokenError:  # firma incorrecta, expirado, mal formado
        raise error

    username = payload.get("sub")
    if username != settings.admin_username:
        raise error
    return username