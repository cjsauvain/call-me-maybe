from typing import Literal


type ParamTypeName = Literal[
    "string", "number", "boolean",
    "null", "array", "object"
]
type ParamTypeValue = str | int | float | bool | dict | list
