from pydantic import BaseModel


class ValidationRule(BaseModel):
    column: str
    rule: str
    threshold: float | None = None
    regex: str | None = None


class ProfileRequest(BaseModel):
    zone: str
    dataset: str
    filename: str

    profile_dimensions: list[str]

    validation_rules: list[ValidationRule]