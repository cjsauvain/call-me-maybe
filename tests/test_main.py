import json

import pytest
from pytest_mock import MockerFixture

from src.function_calling.func_call_input import FuncCallInput
from src.function_calling.func_definitions import FuncDefinitions, ParamModel
from src.main import produce_output


@pytest.fixture
def inputs() -> list[FuncCallInput]:
    return [
        FuncCallInput(prompt="testing")
    ]


@pytest.fixture
def func_definitions() -> list[FuncDefinitions]:
    return [
        FuncDefinitions(
            name="fn",
            description="desc",
            parameters={
                "a": ParamModel(type="string")
            },
            returns=ParamModel(type="null")
        )
    ]


def test_produce_output(
        mocker: MockerFixture,
        inputs: list[FuncCallInput],
        func_definitions: list[FuncDefinitions]
) -> None:
    generate_token = mocker.patch("src.main._generate_tokens")
    decoder = mocker.MagicMock()

    decoder.vocab = [
        "test",
        " string",
        "\"",
        "}",
        "fn\",\"parameters\":{\"a\":\""
    ]
    generate_token.side_effect = [
        ("STR_fn.a", 0, [4]),
        ("STR_fn.a", 1, []),
        ("EXPECT_SEPARATOR_fn.a", 2, []),
        ("ACCEPT", 3, [3])
    ]
    llm_output = produce_output(False, decoder, inputs, func_definitions)
    assert json.loads(llm_output[0]) == \
        {
            "prompt": "testing",
            "name": "fn",
            "parameters": {
                "a": "test string"
            }
        }

    decoder.fsm.get_state.return_value = ""
    decoder.decode.return_value = None
    mocker.stop(generate_token)
    llm_output = produce_output(False, decoder, inputs, func_definitions)
    assert json.loads(llm_output[0]) == \
        {"prompt": "testing", "error": "No valid token found. State: ``"}

    mocker.patch("src.main.MAX_GENERATED_TOKENS", 0)
    llm_output = produce_output(False, decoder, inputs, func_definitions)
    assert json.loads(llm_output[0]) == \
        {"prompt": "testing", "error": "max tokens reached"}
