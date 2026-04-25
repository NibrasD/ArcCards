import os
import json
import subprocess
from web3 import Web3
from dotenv import load_dotenv

# Load from backend/.env
load_dotenv(dotenv_path="backend/.env")

def deploy():
    rpc_url = os.getenv("ARC_RPC_URL")
    private_key = os.getenv("AGENT_PRIVATE_KEY")
    usdc_address = os.getenv("USDC_CONTRACT_ADDRESS")
    
    if not all([rpc_url, private_key, usdc_address]):
        print("Error: Missing environment variables in backend/.env")
        return

    w3 = Web3(Web3.HTTPProvider(rpc_url))
    account = w3.eth.account.from_key(private_key)
    treasury = account.address # Default treasury to deployer
    
    print(f"Deploying from: {account.address}")
    print(f"Arc RPC: {rpc_url}")

    # 1. Compile Contract using vyper CLI
    print("Compiling ArcCardsReceiver.vy...")
    try:
        # Get bytecode
        bytecode = subprocess.check_output(["vyper", "contracts/ArcCardsReceiver.vy"]).decode("utf-8").strip()
        # Get ABI
        abi_json = subprocess.check_output(["vyper", "-f", "abi", "contracts/ArcCardsReceiver.vy"]).decode("utf-8").strip()
        abi = json.loads(abi_json)
    except Exception as e:
        print(f"Compilation failed: {e}")
        return

    # 2. Create Contract Object
    Contract = w3.eth.contract(abi=abi, bytecode=bytecode)

    # 3. Build Transaction
    print("Building deployment transaction...")
    nonce = w3.eth.get_transaction_count(account.address)
    
    # Estimate gas or use a safe limit for Arc Testnet
    construct_txn = Contract.constructor(usdc_address, treasury).build_transaction({
        'from': account.address,
        'nonce': nonce,
        'gas': 3000000,
        'gasPrice': w3.eth.gas_price
    })

    # 4. Sign and Send
    print("Signing and sending transaction...")
    signed_txn = w3.eth.account.sign_transaction(construct_txn, private_key=private_key)
    tx_hash = w3.eth.send_raw_transaction(signed_txn.rawTransaction)
    
    print(f"Transaction sent! Hash: {tx_hash.hex()}")
    print("Waiting for confirmation...")
    
    tx_receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
    contract_address = tx_receipt.contractAddress
    
    print(f"🎉 Contract deployed successfully at: {contract_address}")
    
    # 5. Update .env file
    update_env(contract_address)

def update_env(address):
    env_path = "backend/.env"
    with open(env_path, "r") as f:
        lines = f.readlines()
    
    with open(env_path, "w") as f:
        for line in lines:
            if line.startswith("ARCCARDS_CONTRACT_ADDRESS="):
                f.write(f"ARCCARDS_CONTRACT_ADDRESS={address}\n")
            else:
                f.write(line)
    print(f"Updated {env_path} with new contract address.")

if __name__ == "__main__":
    deploy()
