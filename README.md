# ArcCards: Agentic Nanopayments & Virtual Card Infrastructure

ArcCards is an infrastructure bridge that empowers AI Agents to autonomously issue, fund, and manage Virtual Credit Cards (VCCs) for Real-World Assets (RWA) and Web2 services. Built specifically for the **Agentic Economy on Arc** hackathon, ArcCards utilizes Circle’s Nanopayments infrastructure to settle high-frequency, micro-transactions on the Arc Network (EVM L1) using native USDC.

By leveraging Arc's sub-second finality and negligible gas fees, AI agents can now issue temporary Virtual Cards funded with as little as **$0.01 (Nanopayments)** without gas overhead eroding the margin.

## 🌟 The Problem & The Solution
**The Problem:** AI agents operate in a Web3 ecosystem, but the vast majority of real-world services (cloud computing, SaaS APIs, e-commerce) require traditional Web2 credit cards. 
**The Solution:** ArcCards acts as a decentralized treasury bridge. An AI Agent pays USDC on the Arc Network. Our infrastructure detects the payment and instantly provisions a real Virtual Credit Card via the **Lithic API**, allowing the agent to complete its Web2 purchase seamlessly.

## 🏗️ Technical Architecture (What we built)
ArcCards is not a mock; it is a full-stack, production-grade fintech system comprising 5 core components:

1. **Smart Contract Escrow (Arc EVM):** 
   - A highly secure `ArcCardsReceiver.vy` contract written in Vyper and deployed on Arc Testnet. It receives native USDC payments mapped to unique `order_id` bytes to prevent double-spending.
2. **FastAPI Backend & Policy Engine:** 
   - Manages the order lifecycle state machine (`pending_payment` -> `ordering` -> `delivered`).
   - Built-in **Policy Engine** enforcing per-order and daily spend limits to protect the operator's treasury from rogue agents.
   - Circuit breakers that freeze the system automatically upon detecting repeated fulfillment failures.
3. **On-Chain Event Watcher:** 
   - A persistent, async block-polling service (`watcher.py`) that monitors the Arc blockchain for `PaymentReceived` events. It maintains a block cursor in SQLite to ensure no payments are lost during server restarts.
4. **Lithic VCC Integration:** 
   - A robust HTTP client natively integrated with the **Lithic Sandbox API**. Upon blockchain confirmation, the backend instantly hits Lithic to generate a real Sandbox Visa Card with the exact `spend_limit` matching the agent's USDC payment.
   - Secures card delivery via standard HMAC-SHA256 Webhooks.
5. **Operator Dashboard (Next.js):** 
   - A premium, glassmorphism-styled Admin UI for human operators to monitor their fleet of AI agents.
   - Features real-time stats, live data fetching from FastAPI, and an "Agent Simulator" to manually trigger $0.01 nanopayment orders for testing.

## ⚙️ How It Works (The Lifecycle)
1. **Initiation:** The AI Agent requests a card via `POST /v1/orders/` specifying the amount (e.g., $0.01).
2. **Payment:** The Agent programmatically executes a Web3 transaction, paying the USDC amount to the `ArcCardsReceiver` contract on Arc Testnet.
3. **Detection:** The backend Event Watcher catches the on-chain event in sub-seconds.
4. **Fulfillment:** The backend calls the Lithic API, allocating the exact USD fiat value to a newly generated Virtual Card.
5. **Delivery:** The PAN, CVV, and Expiry are returned to the Agent's Webhook to be used in the real world.

## 🔌 Developer Experience (How Agents Connect)
We engineered ArcCards to have zero friction for AI developers. Connecting an agent to our platform is as simple as:
1. **API Integration:** The agent sends a simple `POST /v1/orders` request to get an invoice.
2. **On-Chain Settlement:** The agent signs an Arc Network transaction using its own wallet.
3. **Card Delivery:** The agent receives the VCC details via Webhook or standard REST polling.

*(Future Roadmap)*: A dedicated NPM/Python SDK (`@arccards/sdk`) where an agent can fund a card in a single line of code: 
`const card = await arccards.fundVirtualCard({ amount: 0.01, wallet: agentWallet });`

## 🚀 Getting Started

### Prerequisites
- Python 3.10+
- Node.js 18+
- Lithic Sandbox API Key

### Backend Setup
```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Update .env with your Lithic Key and Arc Testnet Private Key
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### Frontend Setup
```bash
cd web
npm install
npm run dev
```
Navigate to `http://localhost:3000` to view the live dashboard. You can use the "Simulate Agent" button to trigger an end-to-end $0.01 nanopayment flow directly from the UI.
