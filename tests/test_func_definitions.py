import pytest

from src.function_calling.func_definitions import ParamModel


@pytest.mark.parametrize("schema, error_msg", [
    (
        {"type": "array"},
        'Missing "items" key.'
    ),
    (
        {
            "type": "array",
            "items": {"type": "null"},
            "properties": {
                "name": {
                    "type": "string"
                }
            }
        },
        '"properties" key belongs to objects only.'
    ),
    (
        {"type": "object"},
        'Missing "properties" key.'
    ),
    (
        {
            "type": "object",
            "items": {"type": "null"},
            "properties": {
                "name": {
                    "type": "string"
                }
            }
        },
        '"items" key belongs to arrays only.'
    )
])
def test_invalid_function_definitions(schema: dict, error_msg: str) -> None:
    with pytest.raises(ValueError, match=error_msg):
        ParamModel.model_validate(schema)
