"""
ArcCards API - Main Application
Boots: Express app + Watcher + Reconciler (like Cards402's index.js)
"""

import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1 import orders, webhooks
from app.database import engine, Base
from app.services.watcher import watch_events
from app.services.fulfillment import reconcile_stuck_orders
from app import models
import os
from dotenv import load_dotenv

load_dotenv()

CONTRACT = os.getenv("ARCCARDS_CONTRACT_ADDRESS", "")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Start background services on boot."""
    # Create tables
    Base.metadata.create_all(bind=engine)
    print(f"[BOOT] ArcCards API starting...")
    print(f"[BOOT] Contract: {CONTRACT}")
    print(f"[BOOT] VCC Mode: {os.getenv('VCC_MODE', 'demo')}")

    # Launch watcher + reconciler as background tasks
    watcher_task = asyncio.create_task(watch_events())
    reconciler_task = asyncio.create_task(reconcile_stuck_orders())

    yield

    # Cleanup
    watcher_task.cancel()
    reconciler_task.cancel()


app = FastAPI(
    title="ArcCards API",
    description="Agentic Virtual Card Service on Arc Network",
    version="1.0.0",
    lifespan=lifespan
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routes
app.include_router(orders.router, prefix="/v1/orders", tags=["Orders"])
app.include_router(webhooks.router, prefix="/v1/webhooks", tags=["Webhooks"])


@app.get("/status")
async def status():
    """Health check + circuit breaker state (like Cards402's GET /status)."""
    from app.database import SessionLocal
    db = SessionLocal()
    frozen_row = db.query(models.SystemState).filter(
        models.SystemState.key == "frozen"
    ).first()
    failures_row = db.query(models.SystemState).filter(
        models.SystemState.key == "consecutive_failures"
    ).first()
    db.close()

    return {
        "status": "frozen" if (frozen_row and frozen_row.value == "true") else "ok",
        "frozen": bool(frozen_row and frozen_row.value == "true"),
        "consecutive_failures": int(failures_row.value) if failures_row else 0,
        "version": "1.0.0",
        "network": "arc_testnet",
        "contract": CONTRACT
    }
