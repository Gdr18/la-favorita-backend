from typing import List, Optional

from bson import ObjectId
from pydantic import BaseModel, Field, field_validator, ValidationInfo
from pymongo import ReturnDocument

from src.services.db_services import db


# Funciones para obtener y actualizar los valores permitidos para categorías y alérgenos de productos
def get_allowed_values(name: str) -> list[str]:
    settings_request = db.settings.find_one({"name": name}, {"name": 0, "_id": 0})
    return settings_request.get("values") if settings_request else []


_allowed_allergens = get_allowed_values("allergens")
_allowed_categories = get_allowed_values("categories")


def reload_allowed_values() -> None:
    global _allowed_allergens, _allowed_categories
    _allowed_allergens = get_allowed_values("allergens")
    _allowed_categories = get_allowed_values("categories")


# Campos únicos: name. Está configurado en MongoDB Atlas.
class ProductModel(BaseModel, extra="forbid"):
    name: str = Field(..., min_length=1, max_length=50)
    categories: List[str] = Field(..., min_length=1)
    stock: int = Field(..., ge=0)
    brand: Optional[str] = Field(None, max_length=50)
    allergens: Optional[List[str]] = None
    notes: Optional[str] = Field(None, max_length=500)

    @field_validator("categories", "allergens", mode="before")
    @classmethod
    def __validate_categories_and_allergens(cls, v, field: ValidationInfo):
        field = field.field_name
        if field == "allergens":
            if v is None:
                return v
        if isinstance(v, list) and all(isinstance(i, str) and len(i) > 1 for i in v):
            return cls.checking_in_list(field, v, _allowed_allergens if field == "allergens" else _allowed_categories)
        raise ValueError(
            f"El campo '{field}' debe ser una lista de strings con al menos un caracter en cada string{' o None' if field == 'allergens' else None}."
        )

    @staticmethod
    def checking_in_list(name_field: str, value: list[str], allowed_values: list[str]) -> list[str]:
        invalid_values = [item for item in value if item not in allowed_values if isinstance(value, list)]
        if invalid_values:
            invalid_values_str = ", ".join(f"'{item}'" for item in invalid_values)
            raise ValueError(
                f"""{f"Los valores {invalid_values_str} no son válidos en el campo '{name_field}'." if len(invalid_values) > 1 else f"El valor '{invalid_values[0]}' no es válido en el campo '{name_field}'."}"""
            )
        else:
            return value

    # Solicitudes a la base de datos
    def insert_product(self):
        new_product = db.products.insert_one(self.model_dump())
        return new_product

    @staticmethod
    def get_products():
        products = db.products.find()
        return list(products)

    @staticmethod
    def get_product(product_id):
        product = db.products.find_one({"_id": ObjectId(product_id)}, {"_id": 0})
        return product

    def update_product(self, product_id):
        updated_product = db.products.find_one_and_update(
            {"_id": ObjectId(product_id)}, {"$set": self.model_dump()}, return_document=ReturnDocument.AFTER
        )
        return updated_product

    @staticmethod
    def delete_product(product_id):
        deleted_product = db.products.delete_one({"_id": ObjectId(product_id)})
        return deleted_product
