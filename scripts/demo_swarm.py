import asyncio
import httpx
import uuid
import random
import os
from dotenv import load_dotenv

load_dotenv()

BASE_URL = "http://localhost:8000"
USDC_PRICE = 0.01

async def simulate_agent(agent_id: int):
    agent_wallet = f"0x{uuid.uuid4().hex[:40]}"
    print(f"Agent {agent_id} ({agent_wallet}) starting swarm...")
    
    async with httpx.AsyncClient() as client:
        for i in range(6): # Each agent buys 6 cards
            print(f"Agent {agent_id} | Purchase {i+1}/6")
            
            # 1. Create Order (handles x402 handshake internally in real SDK)
            # Here we simulate sending the payment ID
            headers = {"x-402-payment-id": f"mock_pay_{uuid.uuid4().hex}"}
            payload = {
                "agent_wallet": agent_wallet,
                "amount_usdc": USDC_PRICE
            }
            
            resp = await client.post(f"{BASE_URL}/v1/orders/", json=payload, headers=headers)
            if resp.status_code == 200:
                order_id = resp.json()["id"]
                print(f"Agent {agent_id} | Order Created: {order_id}")
                
                # 2. Simulate On-Chain Payment
                # In real demo, this would use Circle Programmable Wallets to send USDC
                print(f"Agent {agent_id} | Sending 0.01 USDC on Arc...")
                
                # 3. Simulate fulfillment via webhook (for demo speed)
                webhook_payload = {
                    "order_id": order_id,
                    "card_details": {
                        "pan": f"4024 {random.randint(1000, 9999)} {random.randint(1000, 9999)} {random.randint(1000, 9999)}",
                        "cvv": str(random.randint(100, 999)),
                        "expiry": "12/28"
                    }
                }
                # HMAC signing would happen here
                # await client.post(f"{BASE_URL}/v1/webhooks/vcc", json=webhook_payload)
                
            await asyncio.sleep(random.uniform(0.5, 2.0))

async def main():
    print("🚀 Starting ArcCards Swarm Demo (50+ transactions simulation)")
    tasks = [simulate_agent(i) for i in range(10)] # 10 agents
    await asyncio.gather(*tasks)
    print("✅ Swarm Demo Completed.")

if __name__ == "__main__":
    asyncio.run(main())
