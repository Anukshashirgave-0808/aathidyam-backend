from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
import os
from appwrite_client import databases

security = HTTPBearer()

SECRET = os.getenv("JWT_SECRET")
ALGO = os.getenv("JWT_ALGORITHM", "HS256")
DATABASE_ID = os.getenv("DATABASE_ID")
USERS_COLLECTION_ID = os.getenv("USERS_COLLECTION_ID")

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    token = credentials.credentials
    try:
        payload = jwt.decode(token, SECRET, algorithms=[ALGO])
        user_id = payload.get("userId")  # ✅ FIXED

        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token")

        user_doc = databases.get_document(
            DATABASE_ID,
            USERS_COLLECTION_ID,
            user_id
        )
        return user_doc

    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    except Exception as e:
        print("USER FETCH ERROR:", e)
        raise HTTPException(status_code=500, detail="Failed to fetch user")


def get_user_from_token(token: str):
    try:
        payload = jwt.decode(token, SECRET, algorithms=[ALGO])
        user_id = payload.get("userId")  # ✅ FIXED

        if not user_id:
            return None

        return databases.get_document(
            DATABASE_ID,
            USERS_COLLECTION_ID,
            user_id
        )

    except Exception as e:
        print("TOKEN ERROR:", e)
        return None
