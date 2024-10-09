from pydantic import BaseModel, Field, ConfigDict, field_validator
from typing import List


# Campos únicos: name. Está configurado en MongoDB Atlas.
class SettingModel(BaseModel):
    name: str = Field(..., min_length=1, max_length=50)
    values: List[str] = Field(..., min_length=1)

    model_config = ConfigDict(extra='forbid')

    @field_validator("values", mode="before")
    def __validate_values(cls, v):
        if isinstance(v, list) and all(isinstance(item, str) for item in v):
            return v
        raise ValueError("El campo 'values' debe ser una lista de strings")

    def to_dict(self) -> dict:
        return self.model_dump()
