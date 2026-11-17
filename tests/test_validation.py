import pytest
from pytest_mock import MockerFixture

from src.function_calling.validation import json_input_validation


def test_call_input_validation(mocker: MockerFixture) -> None:
    mocker.patch("src.function_calling.validation.load_func_definitions")
    file_reader = mocker.patch("pathlib.Path.read_text")

    with pytest.raises(SystemExit, match="Cannot read"):
        file_reader.side_effect = OSError()
        json_input_validation("", "func_def.json")

    with pytest.raises(SystemExit, match="content is invalid"):
        file_reader.side_effect = None
        file_reader.return_value = '{"name": "What is the sum of 2 and 3?"}'
        json_input_validation("input.json", "func_def.json")

    with pytest.raises(SystemExit, match="Unexpected error"):
        file_reader.side_effect = Exception()
        json_input_validation("input.json", "func_def.json")


def test_func_definitions_validation(mocker: MockerFixture) -> None:
    mocker.patch("src.function_calling.validation.load_func_call_inputs")
    file_reader = mocker.patch("pathlib.Path.read_text")

    with pytest.raises(SystemExit, match="Cannot read"):
        file_reader.side_effect = OSError()
        json_input_validation("input.json", "")

    with pytest.raises(SystemExit, match="content is invalid"):
        file_reader.side_effect = None
        file_reader.return_value = '{"name": "fn_test"}'
        json_input_validation("input.json", "func_def.json")

    with pytest.raises(SystemExit, match="Unexpected error"):
        file_reader.side_effect = Exception()
        json_input_validation("input.json", "func_def.json")
