from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
import json
import httpx
import os

def create_gateway_middleware(price_usd: float, protected_paths: list, circle_api_key: str):
    async def gateway_middleware(request: Request, call_next):
        # Only protect specific paths
        is_protected = any(request.url.path.startswith(path) for path in protected_paths)
        
        if not is_protected:
            return await call_next(request)

        # Check if x402-payment-id header is present
        payment_id = request.headers.get("x-402-payment-id")
        
        if not payment_id:
            # Return 402 Payment Required with Circle Gateway details
            # In a real Circle x402 implementation, you'd generate a payment intent
            return Response(
                content=json.dumps({
                    "error": "Payment Required",
                    "price": price_usd,
                    "currency": "USDC",
                    "payment_gateway": "circle-nanopayments",
                    "instructions": "Submit payment to Circle Nanopayment API to receive a payment ID"
                }),
                status_code=402,
                media_type="application/json"
            )

        # Verify payment_id with Circle (Mocked for now)
        # async with httpx.AsyncClient() as client:
        #     resp = await client.get(f"https://api.circle.com/v1/nanopayments/{payment_id}", headers={"Authorization": f"Bearer {circle_api_key}"})
        #     if resp.status_code != 200:
        #         return Response(content="Invalid Payment ID", status_code=402)

        return await call_next(request)

    return gateway_middleware
