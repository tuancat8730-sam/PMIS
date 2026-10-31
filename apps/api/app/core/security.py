from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

import jwt
from pwdlib import PasswordHash

TOKEN_ISSUER = "pmis-api"
TOKEN_AUDIENCE = "pmis-web"

_password_hash = PasswordHash.recommended()


@dataclass(frozen=True)
class TokenClaims:
    subject: str
    role: str


def hash_password(plain: str) -> str:
    return _password_hash.hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    return _password_hash.verify(plain, hashed)


def create_access_token(
    *,
    subject: str,
    role: str,
    secret: str,
    algorithm: str,
    expires_in: timedelta,
) -> str:
    now = datetime.now(UTC)
    payload = {
        "sub": subject,
        "role": role,
        "iss": TOKEN_ISSUER,
        "aud": TOKEN_AUDIENCE,
        "iat": now,
        "exp": now + expires_in,
    }
    return jwt.encode(payload, secret, algorithm=algorithm)


def decode_access_token(token: str, *, secret: str, algorithm: str) -> TokenClaims:
    """Ném `jwt.InvalidTokenError` khi token hết hạn, sai chữ ký, sai issuer hoặc audience."""
    payload = jwt.decode(
        token,
        secret,
        algorithms=[algorithm],
        audience=TOKEN_AUDIENCE,
        issuer=TOKEN_ISSUER,
        options={"require": ["exp", "iat", "sub", "role"]},
    )
    return TokenClaims(subject=payload["sub"], role=payload["role"])
