from pathlib import Path

from pydantic import TypeAdapter
from src.function_calling.func_call_input import FuncCallInput
from src.function_calling.func_definitions import FuncDefinitions


def load_func_call_inputs(path: Path) -> list[FuncCallInput]:
    return TypeAdapter(
        list[FuncCallInput]
    ).validate_json(
        path.read_text(encoding='utf-8')
    )


def load_func_definitions(path: Path) -> list[FuncDefinitions]:
    return TypeAdapter(
        list[FuncDefinitions]
    ).validate_json(
        path.read_text(encoding='utf-8')
    )
