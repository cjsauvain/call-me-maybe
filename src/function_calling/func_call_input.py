from pydantic import BaseModel, ConfigDict


class FuncCallInput(BaseModel):
    model_config = ConfigDict(extra='forbid')

    prompt: str
