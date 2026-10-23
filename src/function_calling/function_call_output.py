from pydantic import BaseModel, ConfigDict

from src.function_calling.param_types import ParamTypeValue


class FuncCallOutput(BaseModel):
    model_config = ConfigDict(extra='forbid')

    prompt: str
    name: str
    parameters: dict[str, ParamTypeValue]
