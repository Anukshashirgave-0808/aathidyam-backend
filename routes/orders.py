from fastapi import APIRouter, HTTPException, Header, Body
from appwrite_client import tablesDB, _safe_get
from auth.deps import get_user_from_token
import os, uuid

router = APIRouter(prefix="/orders", tags=["Orders"])

DATABASE_ID = os.getenv("DATABASE_ID")
ORDERS_COLLECTION_ID = os.getenv("ORDERS_COLLECTION_ID")


@router.post("/")
def create_order(
    order: dict = Body(...),
    authorization: str | None = Header(None)
):
    try:
        user_id = None
        email = order.get("email")
        is_guest = True

        # ✅ Handle logged-in user
        if authorization:
            token = authorization.replace("Bearer ", "")
            user = get_user_from_token(token)

            if user:
                user_id = _safe_get(user, "$id")
                email = _safe_get(user, "email")
                is_guest = False

        address = order.get("address", {})

        # ✅ Prepare clean data
        order_data = {
            "email": email,
            "isGuest": is_guest,
            "userId": user_id,
            "name": order.get("name"),
            "country": address.get("country"),
            "state": address.get("state"),
            "city": address.get("city"),
            "street": address.get("street"),
            "pincode": address.get("pincode"),
            "phone": order.get("phone"),
            "paymentMethod": order.get("paymentMethod", "COD"),

            # 🔥 FIXED: store items as ARRAY (not string)
            "items": order.get("items", []),

            # 🔥 FIXED: ensure number format
            "total": float(order.get("total", 0)),

            "status": "Pending"
        }

        # ✅ Save to Appwrite
        tablesDB.create_row(
            database_id=DATABASE_ID,
            table_id=ORDERS_COLLECTION_ID,
            row_id=str(uuid.uuid4()),
            data=order_data
        )

        return {
            "success": True,
            "isGuest": is_guest,
            "message": "Order placed successfully"
        }

    except Exception as e:
        print("ORDER ERROR:", e)
        raise HTTPException(status_code=500, detail="Order failed")