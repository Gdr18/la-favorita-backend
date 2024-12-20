from pydantic import BaseModel, Field, model_validator
from src.services.db_services import db
from typing import Union, TypedDict, List, Literal
from pymongo.results import InsertOneResult, DeleteResult
from pymongo import ReturnDocument
from bson import ObjectId
from datetime import datetime


class Items(TypedDict):
    name: str
    qty: int
    custom: str
    price: int


class Address(TypedDict):
    name: Union[str, None]
    line_one: str
    line_two: str
    postal_code: int


class OrderModel(BaseModel, extra="forbid"):
    user_id: str = Field(..., pattern=r"^[a-f0-9]{24}$")
    items: List[Items] = Field(...)
    type_order: Literal["delivery", "collect", "take_away"] = Field(...)
    address: Union[Address, None] = Field(default=None)
    payment: Literal["cash", "card", "paypal"] = Field(...)
    total_price: float = Field(...)
    state: Literal["accepted", "canceled", "cooking", "ready", "sent", "delivered"] = Field(...)
    created_at: datetime = Field(default_factory=datetime.now)

    @model_validator(mode="after")
    def validate_model(self) -> "OrderModel":
        if self.type_order == "delivery" and self.address is None:
            raise (
                "Cuando el campo 'type_order' tiene el valor 'delivery' el campo 'address' debe tener un valor de tipo diccionario"
            )

        return self

    # Solicitudes a la colección order
    def insert_order(self) -> InsertOneResult:
        new_order = db.orders.insert_one(self.model_dump())
        return new_order

    @staticmethod
    def get_orders(skip: int, per_page: int) -> List[dict]:
        orders = db.orders.find().skip(skip).limit(per_page)
        return list(orders)

    @staticmethod
    def get_orders_by_user_id(user_id: str, skip: int, per_page: int) -> List[dict]:
        user_orders = db.orders.find({"user_id": user_id}).skip(skip).limit(per_page)
        return list(user_orders)

    @staticmethod
    def get_order(order_id: str) -> dict:
        order = db.order.find_one({"_id": ObjectId(order_id)}, {"_id": 0})
        return order

    def update_order(self, order_id: str) -> dict:
        updated_order = db.order.find_one_and_update(
            {"_id": ObjectId(order_id)}, {"$set": self.model_dump()}, return_document=ReturnDocument.AFTER
        )
        return updated_order

    @staticmethod
    def delete_order(order_id: str) -> DeleteResult:
        deleted_order = db.order.delete_one({"_id": ObjectId(order_id)})
        return deleted_order
