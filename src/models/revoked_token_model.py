from pydantic import BaseModel, Field
from datetime import datetime


class RevokedTokenModel(BaseModel):
    jti: str = Field(...)
    exp: datetime = Field(...)

    def to_dict(self):
        return self.model_dump()
