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
RESET = "\033[0m"
TOKEN_COLORS = [
    "\033[48;5;124m\033[97m",  # red
    "\033[48;5;130m\033[97m",  # brown-orange
    "\033[48;5;129m\033[97m",  # purple
    "\033[48;5;236m\033[97m",  # gray
    "\033[48;5;22m\033[97m"    # green
]
FORCED_COLOR = "\033[48;5;136m\033[30m"  # dark goldenrod
RED_FG = "\033[38;5;124m"                # red foreground
UNDERLINED = "\033[4m"
CLEAR_EOL = "\033[K"


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


def _build_system_prompt(func_definitions: list[FuncDefinitions]) -> str:
    """Build the system message listing the available functions."""
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
    """Build and encode a chat prompt, followed by the JSON prefix.

    Args:
        model: Model used to encode.
        input: The prompt.
        system_prompt: System message listing the functions.
        json_prefix: Start of the JSON output for the prompt.

    Returns:
        The token ids of the prompt and the JSON prefix.
    """
    formatted_prompt = (
        f"<|im_start|>system\n{system_prompt}<|im_end|>\n"
        f"<|im_start|>user\n{input.prompt}<|im_end|>\n"
        "<|im_start|>assistant\n"
    )

    return model.encode(formatted_prompt + json_prefix)[0].tolist()


def _look_for_generation_errors(
    json_prefix: str,
    generation_state: GenerationState,
    input: FuncCallInput
) -> str:
    """Replace the output of a failed prompt with an error.

    Clears the error afterwards.

    Args:
        json_prefix: JSON generated for the prompt.
        generation_state: Generation progress, holding the error.
        input: The prompt.

    Returns:
        The generated JSON, or an error JSON if the prompt failed.
    """
    if generation_state.error:
        error_dict = {
            "prompt": input.prompt,
            "error": generation_state.error
        }
        json_prefix = json.dumps(error_dict)
        generation_state.error = ""
    return json_prefix


def _display_color_legend() -> None:
    """Print the meaning of the colors used by the visualization."""
    colors_len = len(TOKEN_COLORS)
    legend_width = colors_len + len(": generated_tokens")
    title_padding = legend_width - len("Color Legend:") + 1
    forced_line_padding = legend_width - (
        colors_len + len(": forced tokens")
    ) + 1
    generated_line_padding = legend_width - (
        colors_len + len(": generated tokens")
    ) + 1
    print(f"{RED_FG}┌{"─" * (legend_width + 2)}┐")
    print(
        f"│{RESET} {UNDERLINED}Color Legend:{RESET}"
        f"{" " * title_padding}{RED_FG}│")
    print(
        f"│ {FORCED_COLOR}{" " * colors_len}{RESET}"
        f": forced tokens{" " * forced_line_padding}{RED_FG}│"
    )
    print("│ ", end="")
    for color in TOKEN_COLORS:
        print(f"{color} {RESET}", end="")
    print(f": generated tokens{" " * generated_line_padding}{RED_FG}│")
    print(f"└{"─" * (legend_width + 2)}┘{RESET}\n")


def _display_progress(
    generation_visualization: bool, generation_state: GenerationState,
    constrained_decoder: ConstrainedDecoder, generated_token_id: int,
    forced_ids: list[int], input_count: int, color_idx: int,
    prompt_completed: bool = False
) -> int:
    """Display the generation progress.

    Without visualization, prints the counters on one line.

    With visualization, prints the forced tokens then the generated token,
    each with a background color.

    Args:
        generation_visualization: Whether to show the colored tokens.
        generation_state: Generation progress, holding the counters.
        constrained_decoder: Decoder holding the vocabulary.
        generated_token_id: Id of the token chosen by the model.
        forced_ids: Ids of the tokens forced before it.
        input_count: Number of prompts.
        color_idx: Index of the color for the generated token.
        prompt_completed: Whether the current prompt is completed.

    Returns:
        The index of the color for the next generated token.
    """
    if not generation_visualization:
        print(
            "Generating tokens: "
            f"{generation_state.completed_prompt_count}/{input_count}"
            " prompts completed",
            f"| {generation_state.total_generated_token_count} "
            "tokens generated",
            f"| {generation_state.total_forced_token_count} tokens forced",
            end="\r"
        )
        return color_idx
    if prompt_completed:
        if generation_state.error:
            print(
                f"\n{RED_FG}Error: {generation_state.error}{RESET}",
                end=""
            )
        print("\n")
        return color_idx
    for id in forced_ids:
        print(
            f"{FORCED_COLOR}{constrained_decoder.vocab[id]}{RESET}{CLEAR_EOL}",
            end="", flush=True
        )
    print(
        f"{TOKEN_COLORS[color_idx]}"
        f"{constrained_decoder.vocab[generated_token_id]}{RESET}{CLEAR_EOL}",
        end="", flush=True
    )
    return (color_idx + 1) % len(TOKEN_COLORS)


def _update_generation_status(
    generation_state: GenerationState,
    len_forced_ids: int,
    prompt_completed: bool = False
) -> None:
    """Update the counters after a new token or a completed prompt.

    Args:
        generation_state: Generation progress, updated in place.
        len_forced_ids: Number of tokens forced before the new token.
        prompt_completed: Whether the current prompt is completed. If
            so, counts the prompt and resets the per-prompt counter
            instead of counting tokens.
    """
    if prompt_completed:
        generation_state.completed_prompt_count += 1
        generation_state.prompt_generated_token_count = 0
    else:
        generation_state.prompt_generated_token_count += 1
        generation_state.total_generated_token_count += 1
        generation_state.total_forced_token_count += len_forced_ids


def _generate_tokens(
        constrained_decoder: ConstrainedDecoder,
        current_input_ids: list[int]
) -> tuple[str, int, list[int]]:
    """Generate one token, after adding any forced text.

    Outside a function name, the text forced by the FSM is encoded and
    added to the input ids before asking the model for the next token.

    Args:
        constrained_decoder: Decoder holding the model and the FSM.
        current_input_ids: Token ids, updated in place.

    Returns:
        The new FSM state, the id of the generated token and the
        ids of the forced tokens.

    Raises:
        RuntimeError: If no token is accepted by the FSM.
    """
    forced_ids = []
    generated_tokens = ""
    state = constrained_decoder.fsm.get_state()
    if not constrained_decoder.fsm.is_in_func_name(state):
        generated_tokens = constrained_decoder.retrieve_forced_text()
        if generated_tokens:
            forced_ids.extend(
                constrained_decoder.model.encode(generated_tokens)[0].tolist()
            )
            current_input_ids.extend(forced_ids)
    logits = constrained_decoder.model.get_logits_from_input_ids(
        current_input_ids
    )
    result = constrained_decoder.decode(logits)
    if not result:
        raise RuntimeError(f"No valid token found. State: `{state}`")
    token_id, state = result
    current_input_ids.append(token_id)
    return state, token_id, forced_ids


def produce_output(
    generation_visualization: bool,
    constrained_decoder: ConstrainedDecoder,
    inputs: list[FuncCallInput],
    func_definitions: list[FuncDefinitions],
) -> list[str]:
    """Generate a function call for each prompt, one after the other.

    Args:
        generation_visualization: Whether to show the colored tokens
            instead of the progress line.
        constrained_decoder: Decoder holding the model and the FSM.
        inputs: The prompts.
        func_definitions: Functions shown to the model.

    Returns:
        The JSON text of each function call, or an error JSON for
        each failed prompt.
    """
    generation_state: GenerationState = GenerationState()
    system_prompt: str = _build_system_prompt(func_definitions)
    input_count: int = len(inputs)
    llm_output: list[str] = []
    forced_ids: list[int] = []
    generated_token_id: int = 0
    color_idx: int = 0
    print()
    if generation_visualization:
        _display_color_legend()
    for input in inputs:
        if generation_visualization:
            print(f"{UNDERLINED}prompt: {input.prompt}{RESET}")
        json_prefix = f'{{"prompt":{json.dumps(input.prompt)},"name":"'
        current_input_ids = _build_prompts_ids(
            constrained_decoder.model, input, system_prompt, json_prefix
        )
        state = ""
        constrained_decoder.fsm.set_state(state)
        while state != "ACCEPT":
            if generation_state.prompt_generated_token_count \
                    >= MAX_GENERATED_TOKENS:
                generation_state.error = "max tokens reached"
                break
            try:
                state, generated_token_id, forced_ids = _generate_tokens(
                    constrained_decoder, current_input_ids
                )
            except RuntimeError as e:
                generation_state.error = str(e)
                break
            constrained_decoder.fsm.set_state(state)
            json_prefix += "".join(
                [constrained_decoder.vocab[id] for id in forced_ids]
            ) + constrained_decoder.vocab[generated_token_id]
            _update_generation_status(generation_state, len(forced_ids))
            color_idx = _display_progress(
                generation_visualization, generation_state,
                constrained_decoder, generated_token_id,
                forced_ids, input_count, color_idx
            )
        _update_generation_status(generation_state, len(forced_ids), True)
        color_idx = _display_progress(
            generation_visualization, generation_state,
            constrained_decoder, generated_token_id,
            forced_ids, input_count, color_idx, True
        )
        llm_output.append(
            _look_for_generation_errors(json_prefix, generation_state, input)
        )
    print()
    return llm_output


def main() -> None:
    """Run the program, save the llm output and exit cleanly on errors."""
    try:
        args = parse_cli()

        inputs, func_definitions = json_input_validation(
            args.input, args.function_definitions
        )
        constrained_decoder = ConstrainedDecoder(
            model=Small_LLM_Model(),
            fsm=JSONSchemaFSM(func_definitions=func_definitions)
        )
        llm_output = produce_output(
            args.generation_visualization,
            constrained_decoder, inputs, func_definitions
        )
        save_llm_output(args.output, llm_output)
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
