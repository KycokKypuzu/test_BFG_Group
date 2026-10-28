import json
import uuid

import pytest
import pytest_asyncio
from sqlalchemy import delete, select

from analytics_worker import process_event
from database import engine
from models import stock_agg


@pytest_asyncio.fixture(autouse=True)
async def cleanup_engine():
    yield
    await engine.dispose()


@pytest.mark.asyncio
async def test_receipt_and_issue():
    sku = f"TEST-{uuid.uuid4().hex[:12]}"
    warehouse = "TEST-WH"

    try:
        await process_event(
            "inventory.receipt",
            json.dumps({
                "sku": sku,
                "qty": 100,
                "warehouse": warehouse,
            }),
        )

        await process_event(
            "inventory.issue",
            json.dumps({
                "sku": sku,
                "qty": 30,
                "warehouse": warehouse,
            }),
        )

        async with engine.connect() as conn:
            result = await conn.execute(
                select(stock_agg.c.qty).where(
                    stock_agg.c.sku == sku,
                    stock_agg.c.warehouse == warehouse,
                )
            )

            assert result.scalar_one() == 70

    finally:
        async with engine.begin() as conn:
            await conn.execute(
                delete(stock_agg).where(
                    stock_agg.c.sku == sku,
                    stock_agg.c.warehouse == warehouse,
                )
            )


@pytest.mark.asyncio
async def test_invalid_message():
    sku = f"TEST-{uuid.uuid4().hex[:12]}"
    warehouse = "TEST-WH"

    try:
        await process_event(
            "inventory.receipt",
            json.dumps({
                "sku": sku,
                "qty": -10,
                "warehouse": warehouse,
            }),
        )

        async with engine.connect() as conn:
            result = await conn.execute(
                select(stock_agg.c.qty).where(
                    stock_agg.c.sku == sku,
                    stock_agg.c.warehouse == warehouse,
                )
            )

            assert result.scalar_one_or_none() is None

    finally:
        async with engine.begin() as conn:
            await conn.execute(
                delete(stock_agg).where(
                    stock_agg.c.sku == sku,
                    stock_agg.c.warehouse == warehouse,
                )
            )
