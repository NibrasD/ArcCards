"""
VCC Client - HTTP client for the VCC fulfillment API.

Integrated directly with LITHIC for the Hackathon.
"""

import httpx
import hmac
import hashlib
import time
import os
import json
from dotenv import load_dotenv

load_dotenv()

VCC_MODE = os.getenv("VCC_MODE", "demo")  # "real" or "demo"
VCC_API_BASE = os.getenv("VCC_API_BASE", "https://sandbox.lithic.com/v1")
VCC_TOKEN = os.getenv("VCC_TOKEN", "")
VCC_CALLBACK_SECRET = os.getenv("VCC_CALLBACK_SECRET", "arccards_callback_secret_change_me")
ARCCARDS_BASE_URL = os.getenv("ARCCARDS_BASE_URL", "http://localhost:8000")


class VCCClient:
    def __init__(self):
        self.mode = VCC_MODE
        self.api_base = VCC_API_BASE
        self.token = VCC_TOKEN
        self.callback_secret = VCC_CALLBACK_SECRET
        self.client = httpx.AsyncClient(timeout=30.0)

    async def get_invoice(self, order_id: str, amount_usdc: float) -> dict:
        """
        In the original CTX flow, this asks for an invoice.
        With Lithic, we don't need an invoice, we just create the card.
        We'll mock the invoice step and proceed directly to card creation.
        """
        return {
            "job_id": f"lithic_job_{order_id[:8]}",
            "status": "invoice_issued",
            "amount_usdc": amount_usdc
        }

    async def notify_paid(self, job_id: str) -> dict:
        """
        In the CTX flow, this tells CTX we paid the invoice.
        We'll just return success here.
        """
        return {"status": "fulfilling", "job_id": job_id}

    async def create_lithic_card(self, amount_usdc: float) -> dict:
        """
        Call the real Lithic API to issue a virtual card.
        """
        spend_limit_cents = int(amount_usdc * 100)
        resp = await self.client.post(
            f"{self.api_base}/cards",
            headers={
                "Authorization": self.token,  # Lithic uses just the key or Bearer key
                "Content-Type": "application/json"
            },
            json={
                "type": "VIRTUAL",
                "spend_limit": spend_limit_cents,
                "state": "OPEN"
            }
        )
        
        if not resp.is_success:
            print(f"[LITHIC ERROR] {resp.text}")
            resp.raise_for_status()
            
        data = resp.json()
        
        # Lithic returns the full PAN and CVV only on the initial creation in Sandbox usually,
        # or we might need to fetch it. Sandbox returns it.
        return {
            "number": data.get("pan", "4111111111111111"), # Fallback if hidden
            "cvv": data.get("cvv", "123"),
            "expiry": f"{int(data.get('exp_month', 12)):02d}/{str(data.get('exp_year', '2028'))[-2:]}",
            "brand": "Visa",
            "type": "virtual",
            "lithic_token": data.get("token")
        }

    @staticmethod
    def sign_callback(order_id: str, body: bytes, secret: str) -> tuple:
        timestamp = str(int(time.time() * 1000))
        signed_string = f"{timestamp}.{order_id}.{body.decode()}"
        signature = hmac.new(
            secret.encode(), signed_string.encode(), hashlib.sha256
        ).hexdigest()
        return f"sha256={signature}", timestamp

    @staticmethod
    def verify_callback(signature: str, timestamp: str, order_id: str,
                        body: bytes, secret: str, max_age_ms: int = 600_000) -> bool:
        now = int(time.time() * 1000)
        ts = int(timestamp)
        if abs(now - ts) > max_age_ms:
            return False

        signed_string = f"{timestamp}.{order_id}.{body.decode()}"
        expected = hmac.new(
            secret.encode(), signed_string.encode(), hashlib.sha256
        ).hexdigest()
        expected_sig = f"sha256={expected}"

        return hmac.compare_digest(signature, expected_sig)


# Singleton instance
vcc_client = VCCClient()
