from uuid import UUID

from pydantic import BaseModel, Field


class ProductResponse(BaseModel):
    id: UUID
    sku: str
    qty: int
    warehouse: str
    operation_type: str


class ProductUpdate(BaseModel):
    sku: str
    qty: int = Field(gt=0)
    warehouse: str