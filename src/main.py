from llm_sdk import Small_LLM_Model
from src.function_calling.function_call_input import FuncCallInput
from src.function_calling.function_definitions import FuncDefinitions
from src.function_calling.validation import json_input_validation
from src.parsing.parse_cli import parse_cli


def produce_output(
    inputs: list[FuncCallInput],
    func_definitions: list[FuncDefinitions]
):
    model = Small_LLM_Model()

    print(model.get_pvocab_file())
    # output = []
    # for input in inputs:
    #     input_token_ids = model.encode(input.prompt)


def main() -> None:
    args = parse_cli()

    # Get Prompt + Function definitions
    inputs, func_definitions = json_input_validation(
        args.input, args.function_definitions
    )
    # Produce output using Qwen
    produce_output(inputs, func_definitions)


if __name__ == "__main__":
    main()
