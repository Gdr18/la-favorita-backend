from typing import List, Optional
from pydantic import BaseModel, Field, field_validator, ValidationInfo, ConfigDict

from ..utils.db_utils import db


# Funciones para obtener y actualizar los valores permitidos para categorías y alérgenos de productos
def get_allowed_values(name: str) -> list[str]:
    settings_request = db.settings.find_one({"name": name}, {"name": 0, "_id": 0})
    return settings_request["values"]


allowed_allergens = get_allowed_values("allergens")
allowed_categories = get_allowed_values("categories")


def reload_allowed_values() -> None:
    global allowed_allergens, allowed_categories
    allowed_allergens = get_allowed_values("allergens")
    allowed_categories = get_allowed_values("categories")


# Campos únicos: name. Está configurado en MongoDB Atlas.
class ProductModel(BaseModel):
    name: str = Field(..., min_length=1, max_length=50)
    categories: List[str] = Field(..., min_length=1)
    stock: int = Field(..., ge=0)
    brand: Optional[str] = None
    allergens: Optional[List[str]] = None
    notes: Optional[str] = None

    model_config = ConfigDict(extra='forbid')

    @field_validator('categories', 'allergens', mode='before')
    def __validate_categories_and_allergens(cls, v, field: ValidationInfo):
        field = field.field_name
        if field == 'allergens':
            if v is None:
                return v
        if isinstance(v, list) and all(isinstance(i, str) and len(i) > 1 for i in v):
            return cls.checking_in_list(field, v, allowed_allergens if field == 'allergens' else allowed_categories)
        raise ValueError(f"El campo '{field}' debe ser una lista de strings con al menos un caracter en cada string{' o None' if field == 'allergens' else None}.")

    @staticmethod
    def checking_in_list(name_field: str, value: list[str], allowed_values: list[str]) -> list[str]:
        invalid_values = [item for item in value if item not in allowed_values if isinstance(value, list)]
        if invalid_values:
            invalid_values_str = ', '.join(f"'{item}'" for item in invalid_values)
            raise ValueError(f"""{f"Los valores {invalid_values_str} no son válidos en el campo '{name_field}'." if len(invalid_values) > 1 else f"El valor '{invalid_values[0]}' no es válido en el campo '{name_field}'."}""")
        return value

    def to_dict(self) -> dict:
        return self.model_dump()
