import json
from pathlib import Path

from pydantic import TypeAdapter
from src.function_calling.func_call_input import FuncCallInput
from src.function_calling.func_definitions import FuncDefinitions


def load_func_call_inputs(path: Path) -> list[FuncCallInput]:
    """Load and validate the prompts file.

    Args:
        path: Path of the file.

    Returns:
        The prompts.

    Raises:
        OSError: If the file cannot be read.
        ValidationError: If the content is invalid.
    """
    return TypeAdapter(
        list[FuncCallInput]
    ).validate_json(
        path.read_text(encoding='utf-8')
    )


def load_func_definitions(path: Path) -> list[FuncDefinitions]:
    """Load and validate the function definitions file.

    Args:
        path: Path of the file.

    Returns:
        The function definitions.

    Raises:
        OSError: If the file cannot be read.
        ValidationError: If the content is invalid.
    """
    return TypeAdapter(
        list[FuncDefinitions]
    ).validate_json(
        path.read_text(encoding='utf-8')
    )


def save_llm_output(output_path: str, llm_output: list[str]) -> None:
    """Write the generated function calls to a JSON file.

    Args:
        output_path: Path of the output file.
        llm_output: JSON text of each function call.

    Raises:
        OSError: If the file cannot be written.
        json.JSONDecodeError: If an output is not valid JSON.
    """
    print(f"Saving output to {output_path}...")
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    llm_output = json.loads("[" + ",".join(llm_output) + "]")
    with open(output_path, "w") as file:
        json.dump(llm_output, file, indent=4)
