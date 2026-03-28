from fastapi import APIRouter, Request, HTTPException
from appwrite_client import tablesDB, _safe_get
from appwrite.query import Query
import os

router = APIRouter(prefix="/user", tags=["User"])

DATABASE_ID = os.getenv("DATABASE_ID")
USERS_COLLECTION_ID = os.getenv("USERS_COLLECTION_ID")
ORDERS_COLLECTION_ID = os.getenv("ORDERS_COLLECTION_ID")

@router.get("/current")
def current_user(request: Request):
    """
    Optional route for guest fallback using cookies
    """
    user_id = request.cookies.get("user_id")
    if not user_id:
        return {"status": "guest"}

    try:
        users = tablesDB.list_rows(
            database_id=DATABASE_ID,
            table_id=USERS_COLLECTION_ID,
            queries=[Query.equal("$id", user_id)]
        )
        
        user_rows = _safe_get(users, "rows") or _safe_get(users, "documents") or []
        if not user_rows:
            return {"status": "guest"}

        user = user_rows[0]

        # Fetch past orders
        try:
            orders_resp = tablesDB.list_rows(
                database_id=DATABASE_ID,
                table_id=ORDERS_COLLECTION_ID,
                queries=[Query.equal("userId", user_id)]
            )
            
            order_rows = _safe_get(orders_resp, "rows") or _safe_get(orders_resp, "documents") or []
            orders_list = [
                {
                    "id": _safe_get(o, "$id"),
                    "items": _safe_get(o, "items", []),
                    "total": _safe_get(o, "total", 0),
                    "status": _safe_get(o, "status", "Pending")
                } for o in order_rows
            ]
        except Exception:
            orders_list = []

        return {
            "status": "user",
            "user": {
                "id": _safe_get(user, "$id"),
                "name": _safe_get(user, "name", "User"),
                "email": _safe_get(user, "email", ""),
                "mobile": _safe_get(user, "mobile", ""),
                "role": _safe_get(user, "role", "user")
            },
            "orders": orders_list
        }

    except Exception as e:
        print("CURRENT USER ERROR:", e)
        raise HTTPException(status_code=500, detail="Server error")
