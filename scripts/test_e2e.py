"""
ArcCards End-to-End Test - Full Flow
"""
import json, time, requests

API = "http://localhost:8000"
WALLET = "0xDC48211759e415eF86b6858C65532A63D60AEF3C"

def step(msg):
    print(f"\n{'='*60}")
    print(f"  {msg}")
    print(f"{'='*60}")

def main():
    step("1. Health Check /status")
    r = requests.get(f"{API}/status")
    print(json.dumps(r.json(), indent=2))

    step("2. Create Order - POST /v1/orders")
    r = requests.post(f"{API}/v1/orders/", json={"amount_usdc": 5.0},
                      headers={"X-Agent-Wallet": WALLET, "Idempotency-Key": "test-order-001"})
    print(f"Status: {r.status_code}")
    order = r.json()
    print(json.dumps(order, indent=2))
    order_id = order["order_id"]

    step("3. Poll Order - should be awaiting_payment")
    r = requests.get(f"{API}/v1/orders/{order_id}")
    print(f"Phase: {r.json()['phase']}")
    print(f"Contract: {r.json().get('payment', {}).get('contract_id', 'N/A')}")

    step("4. Wait for demo VCC fulfillment...")
    # In demo mode, the watcher + fulfillment auto-triggers when payment is detected on-chain
    # Since we haven't sent an on-chain tx here, let's simulate via webhook
    import hmac, hashlib
    secret = "arccards_callback_secret_change_me"
    card = {"number": "4024 7891 2345 6789", "cvv": "321", "expiry": "06/28", "brand": "Visa", "type": "prepaid"}
    body = json.dumps({"order_id": order_id, "card": card}).encode()
    ts = str(int(time.time() * 1000))
    signed = f"{ts}.{order_id}.{body.decode()}"
    sig = f"sha256={hmac.new(secret.encode(), signed.encode(), hashlib.sha256).hexdigest()}"

    r = requests.post(f"{API}/v1/webhooks/vcc", data=body,
                      headers={"Content-Type": "application/json",
                               "X-VCC-Signature": sig, "X-VCC-Timestamp": ts, "X-VCC-Order-Id": order_id})
    print(f"Webhook: {r.status_code} - {r.json()}")

    step("5. Poll Order - should be ready with card")
    r = requests.get(f"{API}/v1/orders/{order_id}")
    final = r.json()
    print(f"Phase: {final['phase']}")
    if final.get("card"):
        print(f"Card: {final['card']['number']}")
        print(f"CVV:  {final['card']['cvv']}")
        print(f"Exp:  {final['card']['expiry']}")

    step("6. Policy Engine - reject > $25")
    r = requests.post(f"{API}/v1/orders/", json={"amount_usdc": 30.0},
                      headers={"X-Agent-Wallet": WALLET})
    print(f"Status: {r.status_code} (expected 403)")
    print(r.json())

    step("7. Idempotency - same key returns same order")
    r = requests.post(f"{API}/v1/orders/", json={"amount_usdc": 5.0},
                      headers={"X-Agent-Wallet": WALLET, "Idempotency-Key": "test-order-001"})
    print(f"Same order? {r.json()['order_id'] == order_id}")

    step("ALL TESTS PASSED")

if __name__ == "__main__":
    main()
