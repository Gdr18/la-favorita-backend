from pydantic import BaseModel, Field
from datetime import datetime


# Campo único: "jti", configurado en MongoDB Atlas.
# Campo TTL: "exp", configurado en MongoDB Atlas. El documento se eliminará automáticamente cuando expire la fecha.
class RevokedTokenModel(BaseModel, extra="forbid"):
    jti: str = Field(..., pattern="^[a-f0-9]{8}-[a-f0-9]{4}-4[a-f0-9]{3}-[89ab][a-f0-9]{3}-[a-f0-9]{12}$")
    exp: datetime = Field(...)

    def to_dict(self):
        return self.model_dump()
