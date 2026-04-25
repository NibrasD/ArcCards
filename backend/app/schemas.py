from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime


class OrderCreate(BaseModel):
    amount_usdc: float
    webhook_url: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class RefundInfo(BaseModel):
    stellar_txid: Optional[str] = None


class CardDetails(BaseModel):
    number: str
    cvv: str
    expiry: str
    brand: str = "Visa"
    type: str = "prepaid"


class ContractPayment(BaseModel):
    type: str = "arc_contract"
    contract_id: str
    order_id: str
    amount_usdc: float
    network: str = "arc_testnet"
    chain_id: int = 5042002


class OrderResponse(BaseModel):
    order_id: str
    phase: str
    status: str
    amount_usdc: float
    payment: Optional[ContractPayment] = None
    card: Optional[CardDetails] = None
    refund: Optional[RefundInfo] = None
    tx_hash: Optional[str] = None
    error: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class OrderListResponse(BaseModel):
    orders: list[OrderResponse]
    total: int


class StatusResponse(BaseModel):
    status: str
    frozen: bool
    consecutive_failures: int
    version: str = "1.0.0"
    network: str = "arc_testnet"
    contract: str


class UsageResponse(BaseModel):
    total_spent_usd: float
    spend_limit_usd: float
    daily_spent_usd: float
    daily_limit_usd: float
    orders_today: int
