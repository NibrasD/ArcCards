"""
VCC Callback Webhook - HMAC-verified card delivery.
Mirrors Cards402's api/vcc-callback.js with v2 signature format.
"""

from fastapi import APIRouter, Request, Header, HTTPException, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app import models
from app.services.vcc_client import VCCClient
from app.services.policy_engine import PolicyEngine
import os

router = APIRouter()

VCC_CALLBACK_SECRET = os.getenv("VCC_CALLBACK_SECRET", "arccards_callback_secret_change_me")


@router.post("/vcc")
async def vcc_callback(
    request: Request,
    db: Session = Depends(get_db),
    x_vcc_signature: str = Header(None, alias="X-VCC-Signature"),
    x_vcc_timestamp: str = Header(None, alias="X-VCC-Timestamp"),
    x_vcc_order_id: str = Header(None, alias="X-VCC-Order-Id"),
):
    """
    Receives card details from VCC fulfillment service.
    Verifies HMAC-SHA256 signature with timestamp + order_id (v2 format).
    """
    if not all([x_vcc_signature, x_vcc_timestamp, x_vcc_order_id]):
        raise HTTPException(status_code=401, detail="Missing signature headers")

    body = await request.body()

    # Verify HMAC
    if not VCCClient.verify_callback(
        signature=x_vcc_signature,
        timestamp=x_vcc_timestamp,
        order_id=x_vcc_order_id,
        body=body,
        secret=VCC_CALLBACK_SECRET
    ):
        raise HTTPException(status_code=401, detail="Invalid signature or expired timestamp")

    data = await request.json()
    order_id = data.get("order_id")
    card = data.get("card")

    # Defence against cross-order replay
    if order_id != x_vcc_order_id:
        raise HTTPException(status_code=400, detail="Order ID mismatch")

    if not card:
        raise HTTPException(status_code=400, detail="Missing card details")

    # Update order
    db_order = db.query(models.Order).filter(models.Order.id == order_id).first()
    if not db_order:
        raise HTTPException(status_code=404, detail="Order not found")

    if db_order.status not in ("ordering", "pending_payment"):
        return {"status": "already_processed", "order_id": order_id}

    db_order.status = "delivered"
    db_order.card_details = card
    db.commit()

    # Record success in policy engine (reset circuit breaker)
    policy = PolicyEngine(db)
    policy.record_success()

    print(f"[WEBHOOK] Order {order_id} delivered with card ending ...{card.get('number', '')[-4:]}")

    return {"status": "success", "order_id": order_id}
