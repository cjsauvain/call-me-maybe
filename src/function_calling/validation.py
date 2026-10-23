from pathlib import Path

from pydantic import ValidationError
from src.function_calling.function_call_input import FuncCallInput
from src.function_calling.function_definitions import FuncDefinitions
from src.file_io import load_func_call_inputs, load_func_definitions


def json_input_validation(
    input_file: str,
    func_definitions_file: str
) -> tuple[
        list[FuncCallInput],
        list[FuncDefinitions]
]:
    try:
        inputs = load_func_call_inputs(
            Path(input_file)
        )
    except OSError as e:
        raise SystemExit(f"Cannot read {input_file}: {e.strerror}")
    except ValidationError as e:
        raise SystemExit(f"{input_file} content is invalid: {e}")
    except Exception as e:
        raise SystemExit(f"Unexpected error: {e}")

    try:
        func_definitions = load_func_definitions(
            Path(func_definitions_file)
        )
    except OSError as e:
        raise SystemExit(f"Cannot read {func_definitions_file}: {e.strerror}")
    except ValidationError as e:
        raise SystemExit(f"{func_definitions_file} content is invalid: {e}")
    except Exception as e:
        raise SystemExit(f"Unexpected error: {e}")

    return inputs, func_definitions
