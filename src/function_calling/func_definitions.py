from pydantic import BaseModel, ConfigDict
from src.function_calling.param_types import ParamTypeName


class ParamModel(BaseModel):
    model_config = ConfigDict(extra='forbid')

    type: ParamTypeName


class FuncDefinitions(BaseModel):
    model_config = ConfigDict(extra='forbid')

    name: str
    description: str
    parameters: dict[str, ParamModel]
    returns: ParamModel
