import datetime
import json

from aiohttp import web
from pydantic import ValidationError
from redis.asyncio import Redis
from sqlalchemy import insert, select, func, desc

from database import engine
from models import stock_events, stock_agg
from schemas import ProductUpdate


async def add_receipt(request: web.Request):
    try:
        body = await request.json()
        data = ProductUpdate.model_validate(body)
    except (ValidationError, ValueError, TypeError):
        raise web.HTTPBadRequest(
            text="Invalid request data"
        )

    async with engine.begin() as conn:
        stmt = insert(stock_events).values(
            sku=data.sku,
            qty=data.qty,
            warehouse=data.warehouse,
            operation_type="receipt",
            created_at=datetime.datetime.now(
                datetime.timezone.utc
            ),
        )
        await conn.execute(stmt)

    event = {
        "sku": data.sku,
        "qty": data.qty,
        "warehouse": data.warehouse,
        "operation_type": "receipt",
    }

    await request.app["redis"].publish(
        "inventory.receipt",
        json.dumps(event),
    )

    return web.json_response({
        "message": "Stock events receipt added"
    })


async def add_issue(request: web.Request):
    try:
        body = await request.json()
        data = ProductUpdate.model_validate(body)
    except (ValidationError, ValueError, TypeError):
        raise web.HTTPBadRequest(
            text="Invalid request data"
        )

    async with engine.begin() as conn:
        stmt = insert(stock_events).values(
            sku=data.sku,
            qty=data.qty,
            warehouse=data.warehouse,
            operation_type="issue",
            created_at=datetime.datetime.now(
                datetime.timezone.utc
            ),
        )
        await conn.execute(stmt)

    event = {
        "sku": data.sku,
        "qty": data.qty,
        "warehouse": data.warehouse,
        "operation_type": "issue",
    }

    await request.app["redis"].publish(
        "inventory.issue",
        json.dumps(event),
    )

    return web.json_response({
        "message": "Stock events issue added"
    })



async def get_stock(request: web.Request):
    warehouse = request.query.get("warehouse")
    sku = request.query.get("sku")

    if not warehouse:
        raise web.HTTPBadRequest(text="warehouse is required")

    stmt = (
        select(
            stock_agg.c.sku,
            stock_agg.c.warehouse,
            stock_agg.c.qty,
        )
        .where(stock_agg.c.warehouse == warehouse)
        .order_by(stock_agg.c.sku)
    )

    if sku is not None:
        stmt = stmt.where(stock_agg.c.sku == sku)

    async with engine.connect() as conn:
        result = await conn.execute(stmt)
        rows = result.mappings().all()

    return web.json_response({
        "warehouse": warehouse,
        "stocks": [dict(row) for row in rows],
    })


async def get_stock_summary(request: web.Request):
    try:
        top_n = int(request.query.get("top_n", "5"))
    except ValueError:
        raise web.HTTPBadRequest(text="top_n must be an integer")

    if top_n <= 0:
        raise web.HTTPBadRequest(text="top_n must be positive")

    warehouses_stmt = (
        select(
            stock_agg.c.warehouse,
            func.sum(stock_agg.c.qty).label("total_qty"),
            func.count(stock_agg.c.sku).label("sku_count"),
        )
        .group_by(stock_agg.c.warehouse)
        .order_by(stock_agg.c.warehouse)
    )

    sku_totals = (
        select(
            stock_agg.c.sku,
            func.sum(stock_agg.c.qty).label("total_qty"),
        )
        .group_by(stock_agg.c.sku)
        .subquery()
    )

    top_skus_stmt = (
        select(
            sku_totals.c.sku,
            sku_totals.c.total_qty,
        )
        .order_by(
            desc(sku_totals.c.total_qty),
            sku_totals.c.sku,
        )
        .limit(top_n)
    )

    async with engine.connect() as conn:
        warehouses_result = await conn.execute(warehouses_stmt)
        warehouses = [
            dict(row)
            for row in warehouses_result.mappings().all()
        ]

        top_skus_result = await conn.execute(top_skus_stmt)
        top_skus = [
            dict(row)
            for row in top_skus_result.mappings().all()
        ]

    return web.json_response({
        "warehouses": warehouses,
        "top_skus": top_skus,
    })


async def redis_context(app: web.Application):
    redis = Redis(
        host="localhost",
        port=6379,
        decode_responses=True,
    )

    app["redis"] = redis

    yield

    await redis.aclose()
    await engine.dispose()


app = web.Application()

app.cleanup_ctx.append(redis_context)

app.router.add_post("/receipts", add_receipt)
app.router.add_post("/issues", add_issue)
app.router.add_get("/stock", get_stock)
app.router.add_get("/stock/summary", get_stock_summary)


if __name__ == "__main__":
    web.run_app(app, host="127.0.0.1", port=8000)
