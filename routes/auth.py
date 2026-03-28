from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, EmailStr
from appwrite_client import tablesDB, _safe_get
from appwrite.query import Query
from utils.jwt import create_access_token, decode_access_token
from utils.pwd import hash_password, verify_password
import os, uuid, traceback

router = APIRouter(prefix="/auth", tags=["Auth"])

# ================= ENV =================

DATABASE_ID = os.getenv("DATABASE_ID")
USERS_COLLECTION_ID = os.getenv("USERS_COLLECTION_ID")
ORDERS_COLLECTION_ID = os.getenv("ORDERS_COLLECTION_ID")

class RegisterRequest(BaseModel):
    name: str
    email: EmailStr
    password: str
    mobile: str | None = None


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


# ================= REGISTER =================

@router.post("/register")
def register_user(data: RegisterRequest):
    try:
        users = tablesDB.list_rows(
            database_id=DATABASE_ID,
            table_id=USERS_COLLECTION_ID,
            queries=[Query.equal("email", data.email)]
        )

        if _safe_get(users, "total", 0) > 0:
            raise HTTPException(status_code=400, detail="User already exists")

        if len(data.password) < 8:
            raise HTTPException(status_code=400, detail="Password must be at least 8 characters")

        tablesDB.create_row(
            database_id=DATABASE_ID,
            table_id=USERS_COLLECTION_ID,
            row_id=str(uuid.uuid4()),
            data={
                "name": data.name,
                "email": data.email,
                "mobile": data.mobile,
                "passwordHash": hash_password(data.password),
                "role": "user"
            }
        )

        return {
            "success": True,
            "message": "User registered successfully"
        }

    except Exception as e:
        print("REGISTER ERROR:", e)
        traceback.print_exc()

        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


# ================= LOGIN =================

@router.post("/login")
def login_user(data: LoginRequest):
    try:
        users = tablesDB.list_rows(
            database_id=DATABASE_ID,
            table_id=USERS_COLLECTION_ID,
            queries=[Query.equal("email", data.email)]
        )

        if _safe_get(users, "total", 0) == 0:
            raise HTTPException(status_code=404, detail="User not found")

        user_docs = _safe_get(users, "rows") or _safe_get(users, "documents") or []
        user = user_docs[0] if user_docs else None
        
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        stored_hash = _safe_get(user, "passwordHash")
        if not verify_password(data.password, stored_hash):
            raise HTTPException(status_code=401, detail="Invalid password")

        role = _safe_get(user, "role")

        if role:
            role = role.strip().lower()

        if role not in ["admin", "user"]:
            role = "user"

        guest_orders = tablesDB.list_rows(
            database_id=DATABASE_ID,
            table_id=ORDERS_COLLECTION_ID,
            queries=[
                Query.equal("email", data.email),
                Query.equal("isGuest", True)
            ]
        )

        for order in (_safe_get(guest_orders, "rows") or []):
            tablesDB.update_row(
                database_id=DATABASE_ID,
                table_id=ORDERS_COLLECTION_ID,
                row_id=_safe_get(order, "$id"),
                data={
                    "isGuest": False,
                    "userId": _safe_get(user, "$id")
                }
            )

        token = create_access_token({
            "userId": _safe_get(user, "$id"),
            "email": _safe_get(user, "email"),
            "role": role
        })

        return {
            "success": True,
            "token": token,
            "user": {
                "id": _safe_get(user, "$id"),
                "name": _safe_get(user, "name"),
                "email": _safe_get(user, "email"),
                "mobile": _safe_get(user, "mobile"),
                "role": role
            }
        }

    except Exception as e:
        print("LOGIN ERROR:", e)
        traceback.print_exc()

        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


# ================= MY ORDERS =================

@router.get("/my-orders")
def get_my_orders(token: str):
    try:
        payload = decode_access_token(token)

        user_id = payload.get("userId")
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token")

        orders = tablesDB.list_rows(
            database_id=DATABASE_ID,
            table_id=ORDERS_COLLECTION_ID,
            queries=[
                Query.equal("userId", user_id),
                Query.order_desc("$createdAt")
            ]
        )

        return {
            "success": True,
            "orders": _safe_get(orders, "rows") or []
        }

    except Exception as e:
        print("MY ORDERS ERROR:", e)
        traceback.print_exc()

        raise HTTPException(
            status_code=500,
            detail=str(e)
        )