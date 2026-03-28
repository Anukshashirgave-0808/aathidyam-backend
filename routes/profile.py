from fastapi import APIRouter, Header, HTTPException
from jose import jwt
import os
from appwrite_client import tablesDB, _safe_get
from appwrite.query import Query

router = APIRouter(prefix="/profile", tags=["Profile"])

SECRET = os.getenv("JWT_SECRET")
DATABASE_ID = os.getenv("DATABASE_ID")
USERS_COLLECTION_ID = os.getenv("USERS_COLLECTION_ID")
ORDERS_COLLECTION_ID = os.getenv("ORDERS_COLLECTION_ID")

@router.get("/")
def get_profile(
    authorization: str = Header(None),  # Optional JWT
    email: str = None,                  # Optional fallback
    mobile: str = None                  # Optional fallback
):
    try:
        user = None

        # 1️⃣ Try JWT token first
        if authorization:
            try:
                token = authorization.split(" ")[1]
                payload = jwt.decode(token, SECRET, algorithms=["HS256"])
                user_id = payload["userId"]  # Adjusted to match auth.py token payload
                user_resp = tablesDB.get_row(
                    database_id=DATABASE_ID,
                    table_id=USERS_COLLECTION_ID,
                    row_id=user_id
                )
                user = user_resp
            except Exception as e:
                print("JWT decoding error:", e)
                user = None

        # 2️⃣ Fallback: find by email or mobile
        if not user and (email or mobile):
            queries = []
            if email:
                queries.append(Query.equal("email", email))
            if mobile:
                queries.append(Query.equal("mobile", mobile))

            users_resp = tablesDB.list_rows(
                database_id=DATABASE_ID,
                table_id=USERS_COLLECTION_ID,
                queries=queries
            )

            user_docs = _safe_get(users_resp, "rows") or _safe_get(users_resp, "documents") or []
            if user_docs:
                user = user_docs[0]

        # 3️⃣ If still no user, raise error
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        # Fetch past orders for this user
        try:
            orders_resp = tablesDB.list_rows(
                database_id=DATABASE_ID,
                table_id=ORDERS_COLLECTION_ID,
                queries=[Query.equal("userId", _safe_get(user, "$id"))]
            )
            
            order_rows = _safe_get(orders_resp, "rows") or _safe_get(orders_resp, "documents") or []
            orders_list = [
                {
                    "id": _safe_get(o, "$id"),
                    "items": _safe_get(o, "items", []),
                    "total": _safe_get(o, "total", 0),
                    "status": _safe_get(o, "status", "Pending")
                }
                for o in order_rows
            ]
        except Exception:
            orders_list = []

        return {
            "success": True,
            "user": {
                "id": _safe_get(user, "$id"),
                "name": _safe_get(user, "name", ""),
                "email": _safe_get(user, "email", ""),
                "mobile": _safe_get(user, "mobile", ""),
                "role": _safe_get(user, "role", "user")
            },
            "orders": orders_list
        }

    except Exception as e:
        print("PROFILE ERROR:", e)
        raise HTTPException(status_code=401, detail="Invalid or missing token")
