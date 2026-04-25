import asyncio
import random
from app.database import SessionLocal
from app import models

async def fulfill_vcc_order(order_id: str):
    """
    Simulates the fulfillment of a Virtual Credit Card.
    In a real scenario, this would call a card issuing API or a scraper.
    """
    print(f"Fulfilling order {order_id}...")
    
    # Simulate processing time
    await asyncio.sleep(5)
    
    db = SessionLocal()
    order = db.query(models.Order).filter(models.Order.id == order_id).first()
    
    if order:
        # Generate mock card details
        pan = f"4024 {' '.join([''.join([str(random.randint(0,9)) for _ in range(4)]) for _ in range(3)])}"
        cvv = str(random.randint(100, 999))
        expiry = "12/28"
        
        order.card_details = {
            "pan": pan,
            "cvv": cvv,
            "expiry": expiry,
            "type": "Visa Virtual"
        }
        order.status = "fulfilled"
        db.commit()
        print(f"Order {order_id} fulfilled successfully.")
    
    db.close()
