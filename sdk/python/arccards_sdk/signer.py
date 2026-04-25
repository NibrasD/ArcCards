from web3 import Web3
import os

class CircleWalletSigner:
    """
    Mock implementation of a signer using Circle Programmable Wallets or direct Web3.
    """
    def __init__(self, rpc_url: str, private_key: str):
        self.w3 = Web3(Web3.HTTPProvider(rpc_url))
        self.account = self.w3.eth.account.from_key(private_key)

    async def sign_and_send_payment(self, contract_address: str, order_id: str, amount: float):
        # This would construct the transaction for ArcCardsReceiver.pay_for_order
        # For simplicity, we'll just print and return a mock hash
        print(f"Signing transaction for order {order_id} with amount {amount}")
        return "0x" + "a" * 64
