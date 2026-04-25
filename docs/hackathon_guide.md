# ArcCards: Hackathon Demo Guide

This guide outlines the steps to produce a winning video demo for the Arc x Circle Hackathon.

## 1. Setup Checklist
- [ ] Contract deployed on Arc Testnet.
- [ ] Backend running on public URL (e.g., via ngrok).
- [ ] Circle Developer Console open to show incoming transactions.
- [ ] ArcScan (Explorer) open to show smart contract events.

## 2. Video Demo Script (3-5 Minutes)

### Phase 1: The Problem & Solution (30s)
- Briefly explain that AI agents need a way to spend value in the real world.
- Show **ArcCards**: The first agentic VCC service where USDC is both the gas and the value.

### Phase 2: The x402 Handshake (1m)
- Show the terminal or logs where an agent calls `POST /v1/orders`.
- Highlight the `402 Payment Required` response.
- Show the SDK automatically handling the nanopayment and retrying successfully.
- **Visual**: Show the transaction appearing in the **Circle Nanopayments dashboard**.

### Phase 3: On-Chain Payment (1m)
- Show the agent submitting the USDC transaction to `ArcCardsReceiver.vy`.
- Switch to **ArcScan** to see the `PaymentReceived` event.
- Show the **Event Watcher** logs in the backend detecting the event in real-time.

### Phase 4: Fleet Management (1m)
- Open the **Operator Dashboard**.
- Show the **Policy Engine** in action:
    - Try to create an order > $50 and show the `403 Forbidden` response.
    - Show the **Kill Switch** toggle.
- Show the list of issued cards and audit logs.

### Phase 5: Swarm Demo (Final)
- Run `python scripts/demo_swarm.py`.
- Show 10 agents bombarding the system with 50+ transactions.
- Show the final transaction count on the **Arc Block Explorer**.

## 3. Judging Criteria Highlights
- **Innovation**: Native USDC gas usage on Arc.
- **Completeness**: x402 handshake + On-chain settlement + VCC fulfillment.
- **Scalability**: Swarm demo showing high-throughput agent interaction.
- **Security**: HMAC-signed webhooks and spend policies.
