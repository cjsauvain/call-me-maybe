import json
import sys
from textwrap import dedent

from pydantic import BaseModel

from src.lib.llm_sdk.llm_sdk import Small_LLM_Model
from src.constrained_decoding.constrained_decoder import ConstrainedDecoder
from src.file_io import save_llm_output
from src.function_calling.func_call_input import FuncCallInput
from src.function_calling.func_definitions import FuncDefinitions
from src.function_calling.validation import json_input_validation
from src.parsing.parse_cli import parse_cli
from src.constrained_decoding.json_fsm import JSONSchemaFSM


EXAMPLE_OUTPUT = [
    {
        "prompt": "What is the result of 45 * 21",
        "name": "fn_mul_numbers",
        "parameters": {
            "a": 45,
            "b": 21
        }
    },
    {
        "prompt": "Tell a story for a 3 year-old kid",
        "name": "fn_tell_age_appropriate_story",
        "parameters": {
            "age": 3
        }
    }
]
MAX_GENERATED_TOKENS = 200


class GenerationState(BaseModel):
    """Generation progress of one prompt.

    Attributes:
        state: Current FSM state.
        generated_token_count: Tokens chosen by the model.
        forced_token_count: Tokens forced by the FSM.
        error: Why the generation failed, empty on success.
    """
    state: str = ""
    generated_token_count: int = 0
    forced_token_count: int = 0
    error: str = ""


def _look_for_generation_errors(
    json_prefixes: list[str],
    generation_states: list[GenerationState],
    inputs: list[FuncCallInput]
) -> None:
    """Replace the output of failed prompts with an error.

    Args:
        json_prefixes: JSON of each prompt, updated in place.
        generation_states: Progress of each prompt.
        inputs: The prompts.
    """
    for idx in range(len(json_prefixes)):
        if generation_states[idx].error:
            print(f"Generation error:\n{json_prefixes[idx]}", file=sys.stderr)
            error_dict = {
                "prompt": inputs[idx].prompt,
                "error": generation_states[idx].error
            }
            json_prefixes[idx] = json.dumps(error_dict)


def _update_generation_status(
        len_ignored_indexes: int, input_count: int,
        generation_states: list[GenerationState]
) -> None:
    """Print the generation progress on one line.

    Args:
        len_ignored_indexes: Number of finished prompts.
        input_count: Number of prompts.
        generation_states: Progress of each prompt.
    """
    generated_token_count = sum(
        generation_state.generated_token_count
        for generation_state in generation_states
    )
    forced_token_count = sum(
        [
            generation_state.forced_token_count
            for generation_state in generation_states
        ]
    )
    print(
        f"Generating tokens: {len_ignored_indexes}/{input_count}"
        " prompts completed",
        f"| {generated_token_count} tokens generated",
        f"| {forced_token_count} tokens forced",
        end="\r"
    )


def _save_prompt_generation_state(
    generation_state: GenerationState, state: str, len_force_ids: int
) -> None:
    """Record the new state and token counts of a prompt.

    Args:
        generation_state: Progress to update.
        state: New FSM state.
        len_force_ids: Number of forced tokens.
    """
    generation_state.state = state
    generation_state.generated_token_count += 1
    generation_state.forced_token_count += len_force_ids


def _build_prompts_ids(
    model: Small_LLM_Model,
    inputs: list[FuncCallInput],
    func_definitions: list[FuncDefinitions],
    json_prefixes: list[str]
) -> list[list]:
    """Build and encode the chat prompt of each input.

    Args:
        model: Model used to encode.
        inputs: The prompts.
        func_definitions: Functions shown to the model.
        json_prefixes: Start of the JSON output of each prompt.

    Returns:
        The token ids of each prompt.
    """
    tools = json.dumps([f.model_dump() for f in func_definitions])
    example = json.dumps(EXAMPLE_OUTPUT)
    system_prompt = dedent("""
        You may call one or more functions to assist with the user query.
        You are provided with function signatures
        within <tools></tools> XML tags:
        <tools>
        {tools}
        </tools>
        Your role is to provide the function name and argument(s).
        Example of output:
        {example}
    """).strip().format(tools=tools, example=example)
    formatted_prompts = [
        f"<|im_start|>system\n{system_prompt}<|im_end|>\n"
        f"<|im_start|>user\n{input.prompt}<|im_end|>\n"
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


def _generate_tokens(
        constrained_decoder: ConstrainedDecoder,
        model: Small_LLM_Model,
        current_input_ids: list[int]
) -> tuple[str, str, int]:
    """Generate one token, after adding any forced text.

    Args:
        constrained_decoder: Decoder holding the FSM.
        model: The language model.
        current_input_ids: Token ids, updated in place.

    Returns:
        The new FSM state, the added text and the forced count.

    Raises:
        RuntimeError: If no token is valid or the model fails.
    """
    forced_ids = []
    generated_tokens = ""
    state = constrained_decoder.fsm.get_state()
    if not constrained_decoder.fsm.is_in_func_name(state):
        generated_tokens = constrained_decoder.retrieve_forced_text()
        if generated_tokens:
            forced_ids.extend(model.encode(generated_tokens)[0].tolist())
            current_input_ids.extend(forced_ids)
    logits = model.get_logits_from_input_ids(current_input_ids)
    result = constrained_decoder.decode(logits)
    if not result:
        raise RuntimeError(f"No valid token found. State: `{state}`")
    token_id, state = result
    generated_tokens += constrained_decoder.vocab[token_id]
    current_input_ids.append(token_id)
    return state, generated_tokens, len(forced_ids)


def produce_output(
    output_path: str,
    model: Small_LLM_Model,
    constrained_decoder: ConstrainedDecoder,
    inputs: list[FuncCallInput],
    func_definitions: list[FuncDefinitions],
) -> None:
    """Generate a function call for each prompt and save them.

    Args:
        output_path: Path of the output file.
        model: The language model.
        constrained_decoder: Decoder holding the FSM.
        inputs: The prompts.
        func_definitions: Functions shown to the model.
    """
    input_count = len(inputs)
    generation_states = [GenerationState() for _ in range(input_count)]
    json_prefixes = [
        f'{{"prompt":{json.dumps(input.prompt)},"name":"'
        for input in inputs
    ]
    current_inputs_ids = _build_prompts_ids(
        model, inputs, func_definitions, json_prefixes
    )
    indexes_to_ignore: list[int] = []
    while len(indexes_to_ignore) != len(current_inputs_ids):
        for idx, current_input_ids in enumerate(current_inputs_ids):
            if idx in indexes_to_ignore:
                continue
            if generation_states[idx].generated_token_count \
                    >= MAX_GENERATED_TOKENS:
                indexes_to_ignore.append(idx)
                generation_states[idx].error = "max tokens reached"
                continue
            constrained_decoder.fsm.set_state(generation_states[idx].state)
            try:
                state, generated_tokens, len_forced_ids = _generate_tokens(
                    constrained_decoder, model,
                    current_input_ids
                )
            except RuntimeError as e:
                indexes_to_ignore.append(idx)
                generation_states[idx].error = str(e)
                continue
            json_prefixes[idx] += generated_tokens
            if state == "ACCEPT":
                indexes_to_ignore.append(idx)
            _save_prompt_generation_state(
                generation_states[idx], state,
                len_forced_ids
            )
            _update_generation_status(
                len(indexes_to_ignore), input_count,
                generation_states
            )
    print()
    _look_for_generation_errors(json_prefixes, generation_states, inputs)
    save_llm_output(output_path, json_prefixes)


def main() -> None:
    """Run the program and exit cleanly on errors."""
    try:
        args = parse_cli()

        inputs, func_definitions = json_input_validation(
            args.input, args.function_definitions
        )
        model = Small_LLM_Model()
        constrained_decoder = ConstrainedDecoder(
            model=model,
            fsm=JSONSchemaFSM(func_definitions=func_definitions)
        )
        produce_output(
            args.output, model, constrained_decoder,
            inputs, func_definitions
        )
    except KeyboardInterrupt:
        print()
        print("Exiting generation process...", file=sys.stderr)
        sys.exit(130)
    except Exception as e:
        print()
        print(f"{type(e).__name__}: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
