# Perfect Hackathon Prompt: ArcCards (Arc Network + Circle x402)

"Act as a Lead Web3 Engineer. We are building **ArcCards**, an agentic virtual card platform on **Arc Network** using **Circle's official SDKs**.

### **Objective:**
Enable AI agents to purchase virtual Visa cards ($0.01 fee) using USDC on Arc L1. Implement the full flow: x402 nanopayment -> On-chain escrow -> Event-driven fulfillment -> Policy-governed fleet management.

### **Core Stack:**
1. **Blockchain**: Arc Network (EVM L1), Native USDC for gas/value.
2. **Contracts**: Vyper 0.4.0 (ArcCardsReceiver.vy).
3. **Infrastructure**: Circle Nanopayments (x402), Circle Developer-Controlled Wallets.
4. **Backend**: FastAPI (Python), `circle-titanoboa-sdk`.
5. **Security**: HMAC-signed webhooks, Policy Engine (limits/kill switch).

### **Implementation Steps:**

#### **1. Smart Contract (contracts/)**
- Implement `ArcCardsReceiver.vy` in Vyper 0.4.0.
- Handle `PaymentReceived` events with `bytes32 order_id`.
- Support treasury withdrawals and native USDC logic.

#### **2. Backend & Middleware (backend/)**
- Use `circle-titanoboa-sdk` to implement the x402 gateway.
- Protect `/v1/orders` endpoint; return `402` if unpaid.
- Build a **Policy Engine** for:
    - Daily/Single order spend limits.
    - Global Kill Switch.
    - Approval queues for large transactions.
- Implement `/v1/webhooks/vcc` with **HMAC-SHA256** verification.

#### **3. Event Watcher Service**
- Use `web3.py` to listen for on-chain events on Arc.
- Trigger VCC fulfillment on payment detection.

#### **4. Agent SDK & MCP (sdk/)**
- Python SDK with `ArcCardsClient` handling 402 retries.
- **MCP Server** integration for agent tool access (Claude Desktop).
- `CircleWalletSigner` using Developer-Controlled Wallets API.

#### **5. Swarm Simulation (scripts/)**
- `demo_swarm.py` to simulate 10 agents performing 50+ transactions for stress testing and visual proof of scale.

### **Technical Requirements:**
- Asynchronous Python (async/await) throughout.
- Strict Idempotency using headers.
- Comprehensive `.env.example` with Circle and Arc placeholders."
