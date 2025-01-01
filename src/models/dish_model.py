from pydantic import BaseModel, Field, model_validator, ValidationError
from src.services.db_services import db
from typing import List, Union, Literal, Optional
from typing_extensions import TypedDict, NotRequired
from pymongo.results import InsertOneResult, DeleteResult, UpdateResult
from pymongo import ReturnDocument
from bson import ObjectId
from datetime import datetime


class Ingredients(TypedDict):
    name: str
    allergens: NotRequired[Optional[List[str]]]


class DishModel(BaseModel, extra="forbid"):
    name: str = Field(...)
    category: Literal["starter", "main", "dessert"] = Field(...)
    description: str = Field(...)
    ingredients: List[Ingredients] = Field(...)
    custom: Union[List[dict], None] = Field(default=None)
    price: float = Field(...)
    available: bool = Field(...)
    created_at: datetime = Field(default_factory=datetime.now)

    @model_validator(mode="after")
    def validate_model(self) -> "DishModel":
        ingredients_names = [ingredient["name"] for ingredient in self.ingredients]
        check_ingredients = list(
            db.products.find({"name": {"$in": ingredients_names}}, {"name": 1, "_id": 0, "allergens": 1})
        )
        if len(check_ingredients) != len(ingredients_names):
            raise ValidationError("Alguno de los ingredientes no existe en la colección 'products'.")
        self.ingredients = check_ingredients
        return self

    # Solicitudes a la colección dish
    def insert_dish(self) -> InsertOneResult:
        new_dish = db.dishes.insert_one(self.model_dump())
        return new_dish

    @staticmethod
    def get_dishes(skip: int, per_page: int) -> List[dict]:
        dishes = db.dishes.find().skip(skip).limit(per_page)
        return list(dishes)

    @staticmethod
    def get_dishes_by_category(category: str) -> List[dict]:
        dishes_by_category = db.dishes.find({"category": category})
        return list(dishes_by_category)

    @staticmethod
    def get_dish(dish_id: str) -> dict:
        dish = db.dishes.find_one({"_id": ObjectId(dish_id)}, {"_id": 0})
        return dish

    @staticmethod
    def update_dish(dish_id: str, new_values: dict) -> dict:
        updated_dish = db.dishes.find_one_and_update(
            {"_id": ObjectId(dish_id)}, {"$set": new_values}, return_document=ReturnDocument.AFTER
        )
        return updated_dish

    @staticmethod
    def update_dishes_availability(ingredient: str) -> UpdateResult:
        updated_dishes = db.dishes.update_many({"ingredients": {"$in": ingredient}}, {"$set": {"available": False}})
        return updated_dishes

    @staticmethod
    def delete_dish(dish_id: str) -> DeleteResult:
        deleted_dish = db.dishes.delete_one({"_id": ObjectId(dish_id)})
        return deleted_dish
