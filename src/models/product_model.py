from typing import List, Optional
from pydantic import BaseModel, Field, field_validator, ValidationInfo, ConfigDict


allowed_allergens = [
    "cereal",
    "huevo",
    "crustáceo",
    "pescado",
    "cacahuete",
    "soja",
    "lácteo",
    "fruto de cáscara",
    "apio",
    "mostaza",
    "sésamo",
    "sulfito",
    "altramuz",
    "molusco",
]
allowed_categories = [
    "snack",
    "dulce",
    "fruta",
    "verdura",
    "carne",
    "pescado",
    "lácteo",
    "pan",
    "pasta",
    "arroz",
    "legumbre",
    "huevo",
    "salsa",
    "condimento",
    "especia",
    "aceite",
    "vinagre",
    "bebida alcohólica",
    "bebida no alcohólica",
    "bebida con gas",
    "bebida sin gas",
    "bebida alcohólica fermentada",
    "bebida energética",
    "bebida isotónica",
    "limpieza",
    "otro",
]


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
    def __validate_addresses_basket(cls, v, field: ValidationInfo):
        field = field.field_name
        if field == 'allergens':
            if v is None:
                return v
        if isinstance(v, list) and all(isinstance(i, str) for i in v):
            return cls.checking_in_list(field, v, allowed_allergens if field == 'allergens' else allowed_categories)
        raise ValueError(f"El campo '{field}' debe ser una lista de strings{' o None' if field == 'allergens' else None}.")

    @staticmethod
    def checking_in_list(name_field: str, value: List[str], allowed_values: tuple) -> list:
        invalid_values = [item for item in value if item not in allowed_values if isinstance(value, list)]
        if invalid_values:
            invalid_values_str = ', '.join(f"'{item}'" for item in invalid_values)
            raise ValueError(f"""{f"Los valores {invalid_values_str} no son válidos en el campo '{name_field}'." if len(invalid_values) > 1 else f"El valor '{invalid_values[0]}' no es válido en el campo '{name_field}'."}""")
        return value

    def to_dict(self) -> dict:
        return self.model_dump()
