from typing_extensions import TypedDict
from typing import List, NotRequired


class Ingredient(TypedDict):
    name: str
    allergens: NotRequired[List[str]]
    waste: int


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
