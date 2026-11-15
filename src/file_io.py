import json
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


def save_llm_output(output_path: str, llm_outputs: list[str]) -> None:
    print(f"Saving output to {output_path}...")
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    llm_output = json.loads("[" + ",".join(llm_outputs) + "]")
    with open(output_path, "w") as file:
        json.dump(llm_output, file, indent=4)
