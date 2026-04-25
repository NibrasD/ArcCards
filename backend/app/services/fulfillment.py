"""
Fulfillment Engine - Orchestrates the order lifecycle.
Mirrors Cards402's fulfillment.js pattern.
"""

import asyncio
import os
import json
import time
import httpx
from app.database import SessionLocal
from app import models
from app.services.vcc_client import vcc_client, VCCClient

MAX_FULFILLMENT_ATTEMPTS = 3
STUCK_RETRY_AFTER_S = 120
STUCK_FAIL_AFTER_S = 600

async def handle_payment(order_id: str, tx_hash: str, sender: str, amount: int):
    db = SessionLocal()
    try:
        order = db.query(models.Order).filter(models.Order.id == order_id).first()
        if not order:
            unmatched = models.UnmatchedPayment(
                order_id_attempted=order_id, sender_address=sender, amount=amount, tx_hash=tx_hash
            )
            db.add(unmatched)
            db.commit()
            return
        if order.status != "pending_payment":
            return

        order.status = "ordering"
        order.tx_hash = tx_hash
        order.sender_address = sender
        order.payment_amount = amount
        db.commit()
        print(f"[FULFILLMENT] Order {order_id} -> ordering")
        await _fulfill_order(order_id)
    except Exception as e:
        print(f"[FULFILLMENT] Error handling payment: {e}")
        db.rollback()
    finally:
        db.close()

async def _fulfill_order(order_id: str):
    db = SessionLocal()
    try:
        order = db.query(models.Order).filter(models.Order.id == order_id).first()
        if not order or order.status != "ordering":
            return

        order.fulfillment_attempts = (order.fulfillment_attempts or 0) + 1
        if order.fulfillment_attempts > MAX_FULFILLMENT_ATTEMPTS:
            order.status = "failed"
            order.error = "Max fulfillment attempts exceeded"
            db.commit()
            await _schedule_refund(order_id)
            return

        print(f"[FULFILLMENT] Processing fulfillment for {order_id} using {vcc_client.mode} mode...")
        order.vcc_job_id = f"job_{order_id[:8]}"
        order.vcc_notified_at = int(time.time())
        db.commit()

        if vcc_client.mode == "demo":
            await _demo_self_fulfill(order_id)
        elif vcc_client.mode == "real":
            await _real_lithic_fulfill(order_id, order.amount_usdc)

    except Exception as e:
        print(f"[FULFILLMENT] Error fulfilling {order_id}: {e}")
        order = db.query(models.Order).filter(models.Order.id == order_id).first()
        if order:
            order.error = str(e)
            db.commit()
    finally:
        db.close()

async def _real_lithic_fulfill(order_id: str, amount_usdc: float):
    """
    Real mode: Call Lithic API to issue a card, then trigger internal webhook.
    """
    print(f"[LITHIC] Generating real virtual card for {order_id} (amount: ${amount_usdc})...")
    card_details = await vcc_client.create_lithic_card(amount_usdc)
    print(f"[LITHIC] Success! Card generated. Triggering webhook...")
    
    body = json.dumps({"order_id": order_id, "card": card_details}).encode()
    sig, ts = VCCClient.sign_callback(order_id, body, vcc_client.callback_secret)

    async with httpx.AsyncClient() as client:
        raw_base = os.getenv("ARCCARDS_BASE_URL", "http://localhost:8000")
        base = raw_base.rstrip('/')
        await client.post(
            f"{base}/v1/webhooks/vcc",
            content=body,
            headers={
                "Content-Type": "application/json",
                "X-VCC-Signature": sig,
                "X-VCC-Timestamp": ts,
                "X-VCC-Order-Id": order_id
            }
        )

async def _demo_self_fulfill(order_id: str):
    import random
    await asyncio.sleep(2)
    card_details = {
        "number": f"4024 {random.randint(1000,9999)} {random.randint(1000,9999)} {random.randint(1000,9999)}",
        "cvv": str(random.randint(100, 999)),
        "expiry": f"{random.randint(1,12):02d}/{random.randint(26,29)}",
        "brand": "Visa",
        "type": "prepaid"
    }

    body = json.dumps({"order_id": order_id, "card": card_details}).encode()
    sig, ts = VCCClient.sign_callback(order_id, body, vcc_client.callback_secret)

    async with httpx.AsyncClient() as client:
        base = os.getenv("ARCCARDS_BASE_URL", "http://localhost:8000")
        await client.post(
            f"{base}/v1/webhooks/vcc",
            content=body,
            headers={
                "Content-Type": "application/json",
                "X-VCC-Signature": sig, "X-VCC-Timestamp": ts, "X-VCC-Order-Id": order_id
            }
        )

async def _schedule_refund(order_id: str):
    db = SessionLocal()
    try:
        order = db.query(models.Order).filter(models.Order.id == order_id).first()
        if order: order.status = "refund_pending"
        db.commit()
    finally:
        db.close()

async def reconcile_stuck_orders():
    while True:
        db = SessionLocal()
        try:
            now = int(time.time())
            stuck = db.query(models.Order).filter(models.Order.status == "ordering").all()
            for order in stuck:
                age = now - (order.vcc_notified_at or int(order.created_at.timestamp()))
                if age > STUCK_FAIL_AFTER_S:
                    order.status = "failed"
                    order.error = "Stuck in ordering for too long"
                elif age > STUCK_RETRY_AFTER_S:
                    asyncio.create_task(_fulfill_order(order.id))

            import datetime
            cutoff = datetime.datetime.utcnow() - datetime.timedelta(hours=2)
            expired = db.query(models.Order).filter(
                models.Order.status == "pending_payment", models.Order.created_at < cutoff
            ).all()
            for order in expired: order.status = "expired"

            db.commit()
        except Exception as e:
            db.rollback()
        finally:
            db.close()
        await asyncio.sleep(30)
