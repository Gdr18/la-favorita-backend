from typing import List, NotRequired
from typing_extensions import TypedDict
from datetime import datetime
from bson import ObjectId


class Ingredient(TypedDict):
    name: str
    allergens: NotRequired[List[str]]
    waste: float


class ItemOrder(TypedDict):
    name: str
    qty: int
    ingredients: List[Ingredient]
    price: float


class ItemBasket(TypedDict):
    name: str
    qty: int
    price: float


class Address(TypedDict):
    name: NotRequired[str]
    line_one: str
    line_two: NotRequired[str]
    postal_code: str


def to_json_serializable(obj):
    if isinstance(obj, datetime):
        return obj.isoformat()
    elif isinstance(obj, ObjectId):
        return str(obj)
    elif isinstance(obj, list):
        return [to_json_serializable(item) for item in obj]
    elif isinstance(obj, dict):
        return {k: to_json_serializable(v) for k, v in obj.items()}
    return obj
