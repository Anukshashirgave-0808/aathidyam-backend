from fastapi import APIRouter, HTTPException, Header, Body
from appwrite_client import databases
from auth.deps import get_user_from_token
import os, uuid, json

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

        if authorization:
            token = authorization.replace("Bearer ", "")
            user = get_user_from_token(token)

            if user:
                user_id = user["$id"]  # ✅ FIXED
                email = user["email"]
                is_guest = False

        address = order.get("address", {})

        databases.create_document(
            DATABASE_ID,
            ORDERS_COLLECTION_ID,
            str(uuid.uuid4()),
            {
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
                "items": json.dumps(order.get("items", [])),
                "total": int(order.get("total", 0)),
                "status": "Pending"
            }
        )

        return {"success": True, "isGuest": is_guest}

    except Exception as e:
        print("ORDER ERROR:", e)
        raise HTTPException(500, "Order failed")
