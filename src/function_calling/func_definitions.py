from pydantic import BaseModel, ConfigDict, model_validator
from typing import Literal


type ParamTypeName = Literal[
    "string", "integer", "number", "boolean",
    "null", "array", "object"
]


class ParamModel(BaseModel):
    """JSON schema of a parameter.

    Attributes:
        type: JSON type of the value.
        properties: Schema of each property, for objects.
        items: Schema of the items, for arrays.
    """
    model_config = ConfigDict(extra='forbid')

    type: ParamTypeName
    properties: dict[str, ParamModel] | None = None
    items: ParamModel | None = None

    @model_validator(mode="after")
    def check_nested_fields(self) -> ParamModel:
        """Check that `items` and `properties` match the type.

        Returns:
            The validated model.

        Raises:
            ValueError: If a field is missing or not allowed.
        """
        if self.type == "array" and not self.items:
            raise ValueError("Missing \"items\" key.")
        if self.type != "array" and self.items:
            raise ValueError("\"items\" key belongs to arrays only.")
        if self.type == "object" and not self.properties:
            raise ValueError("Missing \"properties\" key.")
        if self.type != "object" and self.properties:
            raise ValueError("\"properties\" key belongs to objects only.")
        return self


class FuncDefinitions(BaseModel):
    """Definition of a function the model can call.

    Attributes:
        name: Name of the function.
        description: What the function does.
        parameters: Schema of each parameter.
        returns: Schema of the returned value.
    """
    model_config = ConfigDict(extra='forbid')

    name: str
    description: str
    parameters: dict[str, ParamModel]
    returns: ParamModel
