"""
Policy Engine - Spend control rules + approval gating.
Mirrors Cards402's policy.js
"""

from sqlalchemy.orm import Session
from app import models
from fastapi import HTTPException
import datetime


class PolicyEngine:
    def __init__(self, db: Session):
        self.db = db

    def check_system_frozen(self):
        """Check circuit breaker - 3 consecutive failures freezes the system."""
        frozen = self.db.query(models.SystemState).filter(
            models.SystemState.key == "frozen"
        ).first()
        if frozen and frozen.value == "true":
            failures = self.db.query(models.SystemState).filter(
                models.SystemState.key == "consecutive_failures"
            ).first()
            count = int(failures.value) if failures else 0
            raise HTTPException(
                status_code=503,
                detail=f"System frozen after {count} consecutive failures. Contact admin."
            )

    def evaluate(self, agent_wallet: str, amount_usdc: float) -> str:
        """
        Evaluate policy rules for an order.
        Returns: 'approved' | 'pending_approval'
        Raises: HTTPException if rejected outright.
        """
        self.check_system_frozen()

        # Per-order limit
        if amount_usdc > 25.0:
            raise HTTPException(
                status_code=403,
                detail=f"Order amount ${amount_usdc} exceeds per-order limit ($25)"
            )

        # Daily limit check
        today = datetime.datetime.utcnow().date()
        start_of_day = datetime.datetime.combine(today, datetime.time.min)

        daily_orders = self.db.query(models.Order).filter(
            models.Order.agent_wallet == agent_wallet,
            models.Order.status.in_(["ordering", "delivered", "pending_payment"]),
            models.Order.created_at >= start_of_day
        ).all()

        daily_spend = sum(o.amount_usdc for o in daily_orders)
        if daily_spend + amount_usdc > 50.0:
            raise HTTPException(
                status_code=403,
                detail=f"Daily limit exceeded. Spent today: ${daily_spend:.2f}, limit: $50"
            )

        # Orders requiring manual approval (e.g., > $15)
        if amount_usdc > 15.0:
            return "pending_approval"

        return "approved"

    def record_failure(self):
        """Increment consecutive failure counter. Freeze after 3."""
        row = self.db.query(models.SystemState).filter(
            models.SystemState.key == "consecutive_failures"
        ).first()
        if not row:
            row = models.SystemState(key="consecutive_failures", value="0")
            self.db.add(row)
        count = int(row.value) + 1
        row.value = str(count)

        if count >= 3:
            frozen = self.db.query(models.SystemState).filter(
                models.SystemState.key == "frozen"
            ).first()
            if not frozen:
                frozen = models.SystemState(key="frozen", value="true")
                self.db.add(frozen)
            else:
                frozen.value = "true"
            print(f"[POLICY] System FROZEN after {count} consecutive failures")

        self.db.commit()

    def record_success(self):
        """Reset consecutive failure counter on success."""
        row = self.db.query(models.SystemState).filter(
            models.SystemState.key == "consecutive_failures"
        ).first()
        if row:
            row.value = "0"
            self.db.commit()
