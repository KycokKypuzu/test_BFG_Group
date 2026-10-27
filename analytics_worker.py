import asyncio
import json

from pydantic import ValidationError
from redis.asyncio import Redis
from sqlalchemy.dialects.postgresql import insert

from database import engine
from models import stock_agg
from schemas import ProductUpdate


async def process_event(channel: str, payload: str):
    try:
        event = json.loads(payload)
        data = ProductUpdate.model_validate(event)
    except (ValueError, TypeError, ValidationError):
        print(f"Invalid event: {payload}")
        return

    if channel not in ("inventory.receipt", "inventory.issue"):
        return

    delta = data.qty if channel == "inventory.receipt" else -data.qty

    stmt = insert(stock_agg).values(
        sku=data.sku,
        warehouse=data.warehouse,
        qty=delta,
    )

    stmt = stmt.on_conflict_do_update(
        constraint="uq_products_sku_warehouse",
        set_={
            "qty": stock_agg.c.qty + stmt.excluded.qty,
        },
    )

    async with engine.begin() as conn:
        await conn.execute(stmt)

    print(f"{channel}: {data.sku}, {data.warehouse}, {delta:+d}")


async def main():
    redis = Redis(
        host="localhost",
        port=6379,
        decode_responses=True,
    )

    try:
        async with redis.pubsub() as pubsub:
            await pubsub.subscribe(
                "inventory.receipt",
                "inventory.issue",
            )

            print("Worker started")

            async for message in pubsub.listen():
                if message["type"] != "message":
                    continue

                try:
                    await process_event(
                        message["channel"],
                        message["data"],
                    )
                except Exception as exc:
                    print(f"Event processing failed: {exc}")
    finally:
        await redis.aclose()
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
