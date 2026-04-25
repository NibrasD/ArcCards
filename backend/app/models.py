from sqlalchemy import Column, String, Float, Integer, Boolean, DateTime, JSON, Text
from .database import Base
import datetime
import uuid


class Order(Base):
    """
    Order state machine (mirrors Cards402):
    pending_payment -> ordering -> delivered | failed -> refund_pending -> refunded
                    -> expired (no payment after 2h)
    awaiting_approval -> pending_payment | rejected
    """
    __tablename__ = "orders"

    id = Column(String, primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    agent_wallet = Column(String, index=True)
    api_key_id = Column(String, nullable=True, index=True)
    status = Column(String, default="pending_payment", index=True)
    # phase is computed from status (like Cards402)
    amount_usdc = Column(Float)

    # Payment info (from Arc watcher)
    sender_address = Column(String, nullable=True)
    payment_amount = Column(Integer, nullable=True)  # raw USDC amount (6 decimals)
    tx_hash = Column(String, nullable=True, index=True)

    # VCC fulfillment
    vcc_job_id = Column(String, nullable=True)
    vcc_notified_at = Column(Integer, nullable=True)  # unix timestamp
    fulfillment_attempts = Column(Integer, default=0)
    error = Column(Text, nullable=True)

    # Card details (encrypted in production)
    card_details = Column(JSON, nullable=True)

    # Refund
    refund_tx_hash = Column(String, nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    @property
    def phase(self):
        """Maps internal status to agent-facing phase (like Cards402)."""
        mapping = {
            "awaiting_approval": "awaiting_approval",
            "pending_payment": "awaiting_payment",
            "ordering": "processing",
            "delivered": "ready",
            "failed": "failed",
            "refund_pending": "failed",
            "refunded": "refunded",
            "expired": "expired",
            "rejected": "rejected",
        }
        return mapping.get(self.status, self.status)


class UnmatchedPayment(Base):
    """Payments that don't match any known order - for manual review/refund."""
    __tablename__ = "unmatched_payments"

    id = Column(Integer, primary_key=True, autoincrement=True)
    order_id_attempted = Column(String)
    sender_address = Column(String)
    amount = Column(Integer)
    tx_hash = Column(String)
    refunded = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)


class ApiKey(Base):
    """API keys for agents - bcrypt hashed like Cards402."""
    __tablename__ = "api_keys"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    key_prefix = Column(String, index=True)  # first 8 chars for fast lookup
    key_hash = Column(String)  # bcrypt hash
    label = Column(String, nullable=True)
    dashboard_id = Column(String, nullable=True, index=True)
    spend_limit_usd = Column(Float, default=100.0)
    daily_limit_usd = Column(Float, default=50.0)
    per_order_limit_usd = Column(Float, default=25.0)
    total_spent_usd = Column(Float, default=0.0)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)


class SystemState(Base):
    """Global system state - circuit breaker, frozen flag, etc."""
    __tablename__ = "system_state"

    key = Column(String, primary_key=True)
    value = Column(String)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
