from pydantic import BaseModel

class ProfileRequest(BaseModel):
    dataset: str
    rules: dict