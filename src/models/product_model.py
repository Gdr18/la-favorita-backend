from typing import List, Optional
from pydantic import BaseModel, Field, field_validator


allowed_allergens = (
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
)
allowed_category = (
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
)


# Campos únicos: name. Está configurado en MongoDB Atlas.
class ProductModel(BaseModel):
    name: str = Field(..., min_length=1, max_length=50)
    categories: List[str] = Field(...)
    stock: int = Field(..., ge=0)
    brand: Optional[str] = None
    allergens: Optional[List[str]] = None
    notes: Optional[str] = None

    class Config:
        extra = 'forbid'

    @field_validator('categories')
    def __validate_categories(cls, v) -> list:
        checking_value = cls.checking_in_list('categories', v, allowed_category)
        return checking_value

    @field_validator('allergens')
    def __validate_allergens(cls, v):
        if v is None:
            return v
        checking_value = cls.checking_in_list('allergens', v, allowed_allergens)
        return checking_value

    @staticmethod
    def checking_in_list(name_field: str, value: List[str], allowed_values: tuple) -> list:
        invalid_values = [item for item in value if item not in allowed_values]
        if invalid_values:
            invalid_values_str = ', '.join(f"'{item}'" for item in invalid_values)
            allowed_values_str = ', '.join(f"'{item}'" for item in allowed_values)
            raise ValueError(
                f"""{f"Los valores {invalid_values_str} no son válidos en el campo '{name_field}'." if len(invalid_values) > 1 else f"El valor '{invalid_values[0]}' no es válido en el campo '{name_field}'."}"""            # )
            )
        return value

    def to_dict(self) -> dict:
        return self.model_dump()
