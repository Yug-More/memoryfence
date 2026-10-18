from pydantic import BaseModel, ConfigDict


class DomainModel(BaseModel):
    """Immutable, strictly validated model. Unknown fields are rejected."""

    model_config = ConfigDict(frozen=True, strict=True, extra="forbid", validate_default=True)
