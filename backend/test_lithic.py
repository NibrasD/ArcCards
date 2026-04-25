import asyncio
from app.services.vcc_client import vcc_client

async def test_lithic():
    print(f"VCC_MODE: {vcc_client.mode}")
    print(f"API Base: {vcc_client.api_base}")
    try:
        card = await vcc_client.create_lithic_card(10.0)
        print("\nSUCCESS! Lithic returned:")
        print(f"PAN: {card['number']}")
        print(f"CVV: {card['cvv']}")
        print(f"Exp: {card['expiry']}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_lithic())
