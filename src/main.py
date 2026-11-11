from textwrap import dedent

from llm_sdk.llm_sdk import Small_LLM_Model
from src.constrained_decoding.constrained_decoder import ConstrainedDecoder
from src.function_calling.func_call_input import FuncCallInput
from src.function_calling.func_definitions import FuncDefinitions
from src.function_calling.validation import json_input_validation
from src.parsing.parse_cli import parse_cli
from src.constrained_decoding.json_pda import JSONPushdownAutomaton


def produce_output(
    inputs: list[FuncCallInput],
    func_definitions: list[FuncDefinitions]
):
    model = Small_LLM_Model()
    constrained_decoder = ConstrainedDecoder(
        model,
        pda=JSONPushdownAutomaton()
    )

    system_prompt = dedent(f"""
        You may call one or more functions to assist with the user query.
        You are provided with function signatures
        within <tools></tools> XML tags:
        <tools>
        {func_definitions}
        </tools>
        For each function call, return a json object
        with function name and parameter values only (without their types)
        according to the function definition.
    """).strip()
    llm_func_outputs = "["
    for input in inputs:
        print(f"\n{input}")
        formatted_prompt = (
            f"<|im_start|>system\n{system_prompt}<|im_end|>"
            f"<|im_start|>user\n{input.prompt}<|im_end>|"
            "<|im_start|>assistant\n"
        )
        json_prefix = f"{{\"prompt\":\"{input.prompt}\",\"name\":\""
        current_input_ids = model.encode(
            formatted_prompt + json_prefix
        )[0].tolist()
        while True:
            logits = model.get_logits_from_input_ids(current_input_ids)
            candidate_transitions = constrained_decoder.decode(logits)
            max_logit_idx = logits.index(max(logits))
            current_input_ids.append(max_logit_idx)
            json_prefix += model.decode([max_logit_idx])
            state, stack = candidate_transitions[max_logit_idx]
            constrained_decoder.pda.commit_transition(state, stack)
            if not stack:
                break
        llm_func_outputs += json_prefix + ","
        constrained_decoder.pda.reset_state()
        constrained_decoder.pda.reset_stack()


def main() -> None:
    args = parse_cli()

    # Get Prompt + Function definitions
    inputs, func_definitions = json_input_validation(
        args.input, args.func_definitions
    )
    # Produce output using Qwen
    produce_output(inputs, func_definitions)


if __name__ == "__main__":
    main()
