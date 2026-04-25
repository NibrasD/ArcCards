"""
Arc Network Event Watcher - Monitors PaymentReceived events.
Mirrors Cards402's payments/stellar.js with persistent cursor.
"""

import asyncio
from web3 import Web3
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from app.database import SessionLocal
from app import models
from app.services.fulfillment import handle_payment
from dotenv import load_dotenv

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '..', '..', '.env'))

# ABI for PaymentReceived event
ABI = [
    {
        "anonymous": False,
        "inputs": [
            {"indexed": True, "name": "order_id", "type": "bytes32"},
            {"indexed": True, "name": "sender", "type": "address"},
            {"indexed": False, "name": "amount", "type": "uint256"},
            {"indexed": False, "name": "timestamp", "type": "uint256"}
        ],
        "name": "PaymentReceived",
        "type": "event"
    }
]


def get_start_ledger(db) -> int:
    """Persist cursor across restarts (like Cards402's stellar_start_ledger)."""
    row = db.query(models.SystemState).filter(
        models.SystemState.key == "arc_start_block"
    ).first()
    return int(row.value) if row else 0


def save_start_ledger(db, block: int):
    row = db.query(models.SystemState).filter(
        models.SystemState.key == "arc_start_block"
    ).first()
    if not row:
        row = models.SystemState(key="arc_start_block", value=str(block))
        db.add(row)
    else:
        row.value = str(block)
    db.commit()


async def watch_events():
    rpc = os.getenv("ARC_RPC_URL")
    addr = os.getenv("ARCCARDS_CONTRACT_ADDRESS")

    w3 = Web3(Web3.HTTPProvider(rpc))
    contract = w3.eth.contract(address=addr, abi=ABI)

    # Get persisted cursor or start from current block with safety margin
    db = SessionLocal()
    last_block = get_start_ledger(db)
    if last_block == 0:
        # Start 100 blocks back to ensure we don't miss recent txs during deploy
        last_block = max(0, w3.eth.block_number - 100)
        save_start_ledger(db, last_block)
    db.close()

    print(f"[WATCHER] Started on {addr}")
    print(f"[WATCHER] Polling from block {last_block}")

    while True:
        try:
            latest = w3.eth.block_number
            if latest > last_block:
                events = contract.events.PaymentReceived.get_logs(
                    fromBlock=last_block + 1,
                    toBlock=latest
                )

                for event in events:
                    import uuid
                    try:
                        # Try decoding as raw UTF-8 string (our test script sends this)
                        raw_str = event.args.order_id.decode('utf-8').rstrip('\x00')
                        # If it's 32 chars without hyphens, convert to standard UUID string
                        if len(raw_str) == 32:
                            order_id = str(uuid.UUID(raw_str))
                        else:
                            order_id = raw_str
                    except Exception:
                        # Fallback: maybe it's the hex representation of the bytes
                        order_id = event.args.order_id.hex()
                        # If it started with 0x in string form or something else
                        if len(order_id) > 36: # Likely a hex dump
                            try:
                                # Try to see if the database contains this hex
                                pass 
                            except: pass

                    sender = event.args.sender
                    amount = event.args.amount
                    tx_hash = event.transactionHash.hex()

                    print(f"[WATCHER] PaymentReceived: order={order_id}, from={sender}, amount={amount}, tx={tx_hash}")
                    await handle_payment(order_id, tx_hash, sender, amount)

                last_block = latest
                db = SessionLocal()
                save_start_ledger(db, last_block)
                db.close()

        except Exception as e:
            print(f"[WATCHER] Error: {e}")

        await asyncio.sleep(5)


if __name__ == "__main__":
    asyncio.run(watch_events())
