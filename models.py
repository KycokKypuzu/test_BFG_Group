import uuid

from sqlalchemy import MetaData, Table, Column, String, Integer, Uuid, UniqueConstraint, DateTime

metadata = MetaData()

stock_events = Table(
    "stock_events",
    metadata,

    Column(
        "id",
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    ),
    Column("sku", String(50), nullable=False),
    Column("qty", Integer, nullable=False),
    Column("warehouse", String(50), nullable=False),
    Column("operation_type", String(20), nullable=False),
    Column("created_at", DateTime(timezone=True), nullable=False)
)

stock_agg = Table(
    "stock_agg",
    metadata,

    Column(
        "id",
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    ),
    Column("sku", String(50), nullable=False),
    Column("qty", Integer, nullable=False),
    Column("warehouse", String(50), nullable=False),

    UniqueConstraint(
        "sku",
        "warehouse",
        name="uq_products_sku_warehouse",
    ),
)