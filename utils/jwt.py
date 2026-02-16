# utils/jwt.py
from jose import jwt, JWTError, ExpiredSignatureError
import os
from datetime import datetime, timedelta

# --------------------------
# JWT Configuration
# --------------------------
SECRET = os.getenv("JWT_SECRET", "supersecret")  # fallback secret
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 1 day

# --------------------------
# Create access token
# --------------------------
def create_access_token(data: dict, expires_delta: int = ACCESS_TOKEN_EXPIRE_MINUTES):
    """
    Create JWT token with payload data.
    """
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=expires_delta)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET, algorithm=ALGORITHM)
    return encoded_jwt

# --------------------------
# Decode access token
# --------------------------
def decode_access_token(token: str) -> dict:
    """
    Decode JWT token and return payload.
    Raises Exception if token is invalid or expired.
    """
    try:
        payload = jwt.decode(token, SECRET, algorithms=[ALGORITHM])
        return payload
    except ExpiredSignatureError:
        raise Exception("Token expired")
    except JWTError:
        raise Exception("Invalid token")
