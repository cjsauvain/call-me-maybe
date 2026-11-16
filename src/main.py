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


MAX_GENERATED_TOKENS = 80


class GenerationState(BaseModel):
    """Generation progress of the prompts.

    Attributes:
        total_generated_token_count: Tokens chosen by the model,
            over all prompts.
        prompt_generated_token_count: Tokens chosen by the model
            for the current prompt, reset between prompts.
        total_forced_token_count: Tokens forced by the FSM,
            over all prompts.
        completed_prompt_count: Prompts processed, failed ones included.
        error: Why the current prompt failed, empty on success.
    """
    total_generated_token_count: int = 0
    prompt_generated_token_count: int = 0
    total_forced_token_count: int = 0
    completed_prompt_count: int = 0
    error: str = ""


def _look_for_generation_errors(
    json_prefix: str,
    generation_state: GenerationState,
    input: FuncCallInput
) -> str:
    """Replace the output of a failed prompt with an error.

    Prints the partial output on stderr and clears the error.

    Args:
        json_prefix: JSON generated for the prompt.
        generation_state: Generation progress, holding the error.
        input: The prompt.

    Returns:
        The generated JSON, or an error JSON if the prompt failed.
    """
    if generation_state.error:
        print()
        print(f"Generation error:\n{json_prefix}", file=sys.stderr)
        error_dict = {
            "prompt": input.prompt,
            "error": generation_state.error
        }
        json_prefix = json.dumps(error_dict)
        generation_state.error = ""
    return json_prefix


def _update_generation_status(
    generation_state: GenerationState,
    input_count: int,
    len_forced_ids: int,
    prompt_completed: bool = False
) -> None:
    """Count the new tokens and print the progress on one line.

    Args:
        generation_state: Generation progress, updated in place.
        input_count: Number of prompts.
        len_forced_ids: Number of tokens forced before the new token.
    """
    if prompt_completed:
        generation_state.completed_prompt_count += 1
        generation_state.prompt_generated_token_count = 0
    generation_state.prompt_generated_token_count += 1
    generation_state.total_generated_token_count += 1
    generation_state.total_forced_token_count += len_forced_ids
    print(
        "Generating tokens: "
        f"{generation_state.completed_prompt_count}/{input_count}"
        " prompts completed",
        f"| {generation_state.total_generated_token_count} tokens generated",
        f"| {generation_state.total_forced_token_count} tokens forced",
        end="\r"
    )


def _build_system_prompt(func_definitions: FuncDefinitions) -> str:
    return dedent(f"""
        You are provided with function signatures
        within <tools></tools> XML tags:
        <tools>
        {json.dumps([f.model_dump() for f in func_definitions])}
        </tools>
        Your role is to provide the function name and argument(s).
    """).strip()


def _build_prompts_ids(
    model: Small_LLM_Model,
    input: FuncCallInput,
    system_prompt: str,
    json_prefix: str
) -> list[int]:
    """Build and encode a chat prompt.

    Args:
        model: Model used to encode.
        input: The prompt.
        system_prompt: System message listing the functions.
        json_prefix: Start of the JSON output for the prompt.

    Returns:
        The token ids of the prompt.
    """
    formatted_prompt = (
        f"<|im_start|>system\n{system_prompt}<|im_end|>\n"
        f"<|im_start|>user\n{input.prompt}<|im_end|>\n"
        "<|im_start|>assistant\n"
    )

    return model.encode(formatted_prompt + json_prefix)[0].tolist()


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
    """Generate a function call for each prompt, one after the other,
    and save them.

    Args:
        output_path: Path of the output file.
        model: The language model.
        constrained_decoder: Decoder holding the FSM.
        inputs: The prompts.
        func_definitions: Functions shown to the model.
    """
    generation_state = GenerationState()
    system_prompt = _build_system_prompt(func_definitions)
    llm_output = []
    input_count = len(inputs)
    for input in inputs:
        json_prefix = f'{{"prompt":{json.dumps(input.prompt)},"name":"'
        current_input_ids = _build_prompts_ids(
            model, input, system_prompt, json_prefix
        )
        state = ""
        constrained_decoder.fsm.set_state(state)
        while state != "ACCEPT":
            if generation_state.prompt_generated_token_count \
                    >= MAX_GENERATED_TOKENS:
                generation_state.error = "max tokens reached"
                break
            try:
                state, generated_tokens, len_forced_ids = _generate_tokens(
                    constrained_decoder, model,
                    current_input_ids
                )
            except RuntimeError as e:
                generation_state.error = str(e)
                break
            constrained_decoder.fsm.set_state(state)
            json_prefix += generated_tokens
            _update_generation_status(
                generation_state, input_count, len_forced_ids
            )
        _update_generation_status(
            generation_state, input_count, len_forced_ids, True
        )
        llm_output.append(
            _look_for_generation_errors(json_prefix, generation_state, input)
        )
    print()
    save_llm_output(output_path, llm_output)


def main() -> None:
    """Run the program and exit cleanly on errors."""
    try:
        args = parse_cli()

        inputs, func_definitions = json_input_validation(
            args.input, args.function_definitions
        )
        model = Small_LLM_Model(device='cpu')
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
