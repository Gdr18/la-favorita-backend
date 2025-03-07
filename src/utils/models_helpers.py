from typing_extensions import TypedDict
from typing import List, Optional


class Ingredient(TypedDict):
    name: str
    allergens: Optional[List[str]]
    waste: int


class ItemOrder(TypedDict):
    name: str
    qty: int
    ingredients: List[Ingredient]
    price: float


class Address(TypedDict):
    name: Optional[str]
    line_one: str
    line_two: Optional[str]
    postal_code: str
