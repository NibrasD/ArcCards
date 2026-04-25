from mcp.server.fastmcp import FastMCP
from .client import ArcCardsClient
from .signer import CircleWalletSigner
import os

# Initialize MCP Server
mcp = FastMCP("ArcCards")

# Configuration (In production, these come from env or config)
RPC_URL = os.getenv("ARC_RPC_URL", "https://rpc.testnet.arc.network")
API_URL = os.getenv("ARCCARDS_API_URL", "http://localhost:8000")
PRIVATE_KEY = os.getenv("AGENT_PRIVATE_KEY")

signer = CircleWalletSigner(RPC_URL, PRIVATE_KEY) if PRIVATE_KEY else None
client = ArcCardsClient(API_URL, signer)

@mcp.tool()
async def issue_virtual_card(amount: float = 0.01) -> str:
    """
    Issues a new virtual Visa card using USDC on Arc Network.
    Costs $0.01 fee per card.
    """
    if not signer:
        return "Error: Agent wallet not configured (PRIVATE_KEY missing)."
    
    try:
        # 1. Create Order
        order = await client.create_order(signer.account.address, amount)
        order_id = order["id"]
        
        # 2. Pay on-chain
        contract_addr = os.getenv("ARCCARDS_CONTRACT_ADDRESS")
        tx_hash = await client.pay_for_card(contract_addr, order_id, amount)
        
        return f"Successfully initialized card issuance. Order ID: {order_id}. Tx Hash: {tx_hash}. Poll status to get card details."
    except Exception as e:
        return f"Failed to issue card: {str(e)}"

@mcp.tool()
async def get_card_details(order_id: str) -> str:
    """
    Retrieves the virtual card details for a completed order.
    """
    try:
        order = await client.get_order_status(order_id)
        if order["status"] == "fulfilled":
            details = order["card_details"]
            return f"Card Details: PAN {details['pan']}, CVV {details['cvv']}, Expiry {details['expiry']}"
        else:
            return f"Order status: {order['status']}. Please wait for fulfillment."
    except Exception as e:
        return f"Error retrieving card: {str(e)}"

if __name__ == "__main__":
    mcp.run()
