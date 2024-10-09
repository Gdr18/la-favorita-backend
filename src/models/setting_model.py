from pydantic import BaseModel, Field, ConfigDict
from typing import List


class SettingModel(BaseModel):
    name: str = Field(..., min_length=1, max_length=50)
    values: List[str] = Field(..., min_length=1)

    model_config = ConfigDict(extra='forbid')

    def to_dict(self) -> dict:
        return self.model_dump()
