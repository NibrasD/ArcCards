"""
ArcCards True E2E Test (Lithic Integration)
1. Create order via API (x402 handshake)
2. Send USDC to contract on Arc Testnet
3. Watcher detects payment -> triggers Lithic
4. Poll API to get the real Sandbox Visa Card
"""
import os, json, time, requests
from web3 import Web3
from dotenv import load_dotenv

load_dotenv(dotenv_path="backend/.env")

API = os.getenv("ARCCARDS_BASE_URL", "http://localhost:8000")
RPC = os.getenv("ARC_RPC_URL")
PK = os.getenv("AGENT_PRIVATE_KEY")
CONTRACT = os.getenv("ARCCARDS_CONTRACT_ADDRESS")

w3 = Web3(Web3.HTTPProvider(RPC))
account = w3.eth.account.from_key(PK)

ABI = [
    {
        "inputs": [
            {"name": "order_id", "type": "bytes32"},
            {"name": "amount", "type": "uint256"}
        ],
        "name": "pay_for_order",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function"
    }
]

def step(msg):
    print(f"\n{'='*60}")
    print(f"  {msg}")
    print(f"{'='*60}")

def main():
    step("1. Health Check & Config")
    r = requests.get(f"{API}/status")
    print(json.dumps(r.json(), indent=2))

    step("2. Create Order - POST /v1/orders")
    r = requests.post(
        f"{API}/v1/orders/", 
        json={"amount_usdc": 1.0},
        headers={"X-Agent-Wallet": account.address}
    )
    order = r.json()
    order_id = order["order_id"]
    print(f"Order ID: {order_id}")
    print(f"Phase: {order['phase']}")

    step("3. Pay On-Chain (Arc Testnet) -> Triggers Lithic")
    contract = w3.eth.contract(address=CONTRACT, abi=ABI)
    
    # order_id is a UUID string, convert to bytes32
    order_bytes32 = order_id.replace('-', '').encode('utf-8')[:32].ljust(32, b'\0')
    
    amount_wei = 1000000 # 1 USDC (assuming 6 decimals)
    
    usdc_addr = os.getenv("USDC_CONTRACT_ADDRESS", "0x3600000000000000000000000000000000000000")
    erc20_abi = [{"constant":False,"inputs":[{"name":"_spender","type":"address"},{"name":"_value","type":"uint256"}],"name":"approve","outputs":[{"name":"","type":"bool"}],"type":"function"}]
    usdc_contract = w3.eth.contract(address=usdc_addr, abi=erc20_abi)
    
    print("Approving USDC...")
    try:
        nonce = w3.eth.get_transaction_count(account.address)
        approve_tx = usdc_contract.functions.approve(CONTRACT, amount_wei).build_transaction({
            'from': account.address,
            'nonce': nonce,
            'gas': 100000,
            'gasPrice': w3.eth.gas_price,
        })
        signed_approve = w3.eth.account.sign_transaction(approve_tx, PK)
        w3.eth.send_raw_transaction(signed_approve.rawTransaction)
        nonce += 1
    except Exception as e:
        print(f"Approve skipped or failed: {e}")
        nonce = w3.eth.get_transaction_count(account.address)
    
    print("Building pay_for_order transaction...")
    tx = contract.functions.pay_for_order(order_bytes32, amount_wei).build_transaction({
        'from': account.address,
        'nonce': nonce,
        'gas': 300000,
        'gasPrice': w3.eth.gas_price,
    })
    
    print("Signing and sending...")
    signed_tx = w3.eth.account.sign_transaction(tx, PK)
    tx_hash = w3.eth.send_raw_transaction(signed_tx.rawTransaction)
    print(f"Tx Hash: {tx_hash.hex()}")
    
    print("Waiting for transaction confirmation...")
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
    print(f"Status: {receipt.status} (1=Success)")

    step("4. Polling API for Real Lithic Card")
    # The Watcher will pick it up and hit Lithic, then trigger the webhook
    for i in range(15):
        time.sleep(3)
        r = requests.get(f"{API}/v1/orders/{order_id}")
        final = r.json()
        print(f"Poll {i+1}... Phase: {final['phase']}")
        if final.get("card"):
            print("\n🎉 SUCCESS! Received Real Sandbox Card from Lithic:")
            print(f"PAN:  {final['card']['number']}")
            print(f"CVV:  {final['card']['cvv']}")
            print(f"Exp:  {final['card']['expiry']}")
            break

if __name__ == "__main__":
    main()
