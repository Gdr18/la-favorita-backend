from datetime import datetime

from pydantic import BaseModel, Field, field_validator


# Campo único: "jti" y "user_id", configurado en MongoDB Atlas.
# Campo TTL: "expires_at", configurado en MongoDB Atlas. El documento se eliminará automáticamente cuando expire la fecha.
# TODO: Probar si funciona datetime.
class TokenModel(BaseModel, extra="forbid", arbitrary_types_allowed=True):
    user_id: str = Field(..., pattern=r"^[a-f0-9]{24}$")
    jti: str = Field(..., pattern=r"^[a-f0-9]{8}-[a-f0-9]{4}-4[a-f0-9]{3}-[89ab][a-f0-9]{3}-[a-f0-9]{12}$")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: datetime = Field(...)

    @field_validator("exp", mode="before")
    @classmethod
    def check_exp(cls, v):
        if isinstance(v, int) and len(str(v)) == 10 and v > datetime.utcnow().timestamp():
            return datetime.utcfromtimestamp(v)
        raise ValueError("El campo 'exp' debe ser de tipo unix timestamp y mayor que la fecha actual")

    def to_dict(self):
        return self.model_dump()
