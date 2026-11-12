import json
from textwrap import dedent

from llm_sdk.llm_sdk import Small_LLM_Model
from src.constrained_decoding.constrained_decoder import ConstrainedDecoder
from src.function_calling.func_call_input import FuncCallInput
from src.function_calling.func_definitions import FuncDefinitions
from src.function_calling.validation import json_input_validation
from src.parsing.parse_cli import parse_cli
from src.constrained_decoding.json_pda import JSONPushdownAutomaton


def _build_prompts_ids(
    model: Small_LLM_Model,
    inputs: list[FuncCallInput],
    func_definitions: list[FuncDefinitions],
    json_prefixes: list[str]
):
    system_prompt = dedent(f"""
        You may call one or more functions to assist with the user query.
        You are provided with function signatures
        within <tools></tools> XML tags:
        <tools>
        {func_definitions}
        </tools>
    """).strip()
    formatted_prompts = [
        f"<|im_start|>system\n{system_prompt}<|im_end|>"
        f"<|im_start|>user\n{input.prompt}<|im_end>|"
        "<|im_start|>assistant\n"
        for input in inputs
    ]
    current_inputs_ids = []
    for formatted_prompt, json_prefix in zip(formatted_prompts, json_prefixes):
        current_inputs_ids.append(
            model.encode(
                formatted_prompt + json_prefix
            )[0].tolist()
        )

    return current_inputs_ids


def produce_output(
    model: Small_LLM_Model,
    constrained_decoder: ConstrainedDecoder,
    inputs: list[FuncCallInput],
    func_definitions: list[FuncDefinitions],
):
    input_count = len(inputs)
    json_prefixes = [
        f"{{\"prompt\":\"{input.prompt}\",\"name\":\""
        for input in inputs
    ]
    current_inputs_ids = _build_prompts_ids(
        model, inputs, func_definitions, json_prefixes
    )
    input_states = [("", "FUNC_NAME") for _ in range(input_count)]
    indexes_to_ignore = []
    token_count = 0
    while len(indexes_to_ignore) != len(current_inputs_ids):
        for idx, current_input_ids in enumerate(current_inputs_ids):
            if idx in indexes_to_ignore:
                continue
            logits = model.get_logits_from_input_ids(current_input_ids)
            constrained_decoder.pda.set_state(input_states[idx][0])
            constrained_decoder.pda.set_transition_category(
                input_states[idx][1]
            )
            candidate_transitions = constrained_decoder.decode(logits)
            if not candidate_transitions:
                raise RuntimeError(
                    "No valid token found.\n"
                    f"State: {constrained_decoder.pda.get_state()}\n"
                    "Category: "
                    f"{constrained_decoder.pda.get_transition_category()}"
                )
            max_logit_idx = logits.index(max(logits))
            current_input_ids.append(max_logit_idx)
            json_prefixes[idx] += model.decode([max_logit_idx])
            state = candidate_transitions[max_logit_idx]
            if state == "ACCEPT":
                indexes_to_ignore.append(idx)
                json_prefixes[idx] += "}"
            elif "ACCEPT_" in state:
                constrained_decoder.pda.set_transition_category(
                    state.removeprefix("ACCEPT_")
                )
                state = ""
            input_states[idx] = (
                state, constrained_decoder.pda.get_transition_category()
            )
            token_count += 1
            generation_status = (
                f"Generating: {len(indexes_to_ignore)}/{input_count}"
                " prompts completed "
                f"| {token_count} tokens generated"
            )
            print(generation_status, end="\r")
    llm_func_outputs = "[" + ",".join(json_prefixes) + "]"
    with open("./data/output.json", "w") as file:
        json.dump(llm_func_outputs, file, indent=4)


def main() -> None:
    args = parse_cli()

    func_definitions_path = args.func_definitions
    # Get prompts + function definitions
    inputs, func_definitions = json_input_validation(
        args.input, func_definitions_path
    )
    # Produce output
    model = Small_LLM_Model()
    constrained_decoder = ConstrainedDecoder(
        model,
        pda=JSONPushdownAutomaton(func_definitions_path)
    )
    produce_output(
        model, constrained_decoder,
        inputs, func_definitions
    )


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"{type(e).__name__}: {e}")
