import httpx
import json
from .signer import CircleWalletSigner

class ArcCardsClient:
    def __init__(self, base_url: str, signer: CircleWalletSigner):
        self.base_url = base_url
        self.signer = signer
        self.client = httpx.AsyncClient(base_url=base_url)

    async def create_order(self, agent_wallet: str, amount: float):
        """
        Creates an order, handling the x402 handshake automatically.
        """
        # Initial attempt - should return 402
        payload = {
            "agent_wallet": agent_wallet,
            "amount_usdc": amount
        }
        
        response = await self.client.post("/v1/orders/", json=payload)
        
        if response.status_code == 402:
            print("x402 Payment Required. Handling nanopayment...")
            # Here you would use Circle Nanopayments to pay the fee
            # For this demo, we assume the agent pays the fee and gets a payment ID
            payment_id = "mock_payment_id_from_circle" # This would come from Circle SDK
            
            # Retry with payment ID
            headers = {"x-402-payment-id": payment_id}
            response = await self.client.post("/v1/orders/", json=payload, headers=headers)
            
        response.raise_for_status()
        return response.json()

    async def get_order_status(self, order_id: str):
        response = await self.client.get(f"/v1/orders/{order_id}")
        response.raise_for_status()
        return response.json()

    async def pay_for_card(self, contract_address: str, order_id: str, amount: float):
        """
        Submits the USDC transaction to the Arc Network contract.
        """
        # In a real SDK, this would use web3.py or Circle Programmable Wallets SDK
        # to sign and broadcast a transaction to the ArcCardsReceiver contract.
        print(f"Agent signing transaction to pay {amount} USDC to {contract_address} for order {order_id}...")
        tx_hash = await self.signer.sign_and_send_payment(contract_address, order_id, amount)
        return tx_hash
