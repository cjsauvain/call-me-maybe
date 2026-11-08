import json
from textwrap import dedent
from typing import Callable

from llm_sdk.llm_sdk import Small_LLM_Model
from src.function_calling.function_call_input import FuncCallInput
from src.function_calling.function_definitions import FuncDefinitions
from src.function_calling.validation import json_input_validation
from src.parsing.parse_cli import parse_cli


def _load_json_file(path_provider: Callable) -> dict[str, int]:
    path = path_provider()
    with open(path, "r") as file:
        data = json.load(file)

    return data


def produce_output(
    inputs: list[FuncCallInput],
    func_definitions: list[FuncDefinitions]
):
    model = Small_LLM_Model()

    output = []
    tokenizer_config = _load_json_file(model.get_path_to_tokenizer_file)
    # bot_token_id = next(
    #     (
    #         token_dict["id"]
    #         for token_dict in tokenizer_config["added_tokens"]
    #         if token_dict["content"] == "<|im_start|>"
    #     ),
    #     151644
    # )
    eot_token_id = next(
        (
            token_dict["id"]
            for token_dict in tokenizer_config["added_tokens"]
            if token_dict["content"] == "<|im_end|>"
        ),
        151645
    )
    # btc_token_id = next(
    #     (
    #         token_dict["id"]
    #         for token_dict in tokenizer_config["added_tokens"]
    #         if token_dict["content"] == "<tool_call>"
    #     ),
    #     151657
    # )
    # etc_token_id = next(
    #     (
    #         token_dict["id"]
    #         for token_dict in tokenizer_config["added_tokens"]
    #         if token_dict["content"] == "</tool_call>"
    #     ),
    #     151658
    # )
    # system_prompt = dedent("""
    #     <|im_start|>system
    #     You may call one or more functions to assist with the user query.
    #     You are provided with function signatures
    #     within <tools></tools> XML tags:
    #     <tools>
    #     {{JSON Schema of function 1}}
    #     {{JSON Schema of function 2}}
    #     </tools>
    # """).strip()
    system_prompt = dedent("""
        <|im_start|>systemYou are my Assistant.
        Please answer my questions.<|im_end|>
    """).strip()
    current_input_ids = model.encode(system_prompt)[0].tolist()
    for i, input in enumerate(inputs):
        formatted_user_prompt = (
            f"<|im_start|>user{input.prompt}<|im_end|><|im_start|>assistant"
        )
        print(f"\n{i}: {input}")
        len = 0
        max_logit_idx = eot_token_id - 1
        input_tensor = model.encode(formatted_user_prompt)
        current_input_ids.extend(input_tensor[0].tolist())
        while max_logit_idx != eot_token_id:
            logits = model.get_logits_from_input_ids(current_input_ids)
            max_logit_idx = logits.index(max(logits))
            token = model.decode([max_logit_idx])
            output.append(token)
            current_input_ids.append(max_logit_idx)
            print(token, end="", flush=True)
            if len > 200:
                break
            len += 1
        print()


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
