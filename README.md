*This project has been created as part of the 42 curriculum by jsauvain.*

# call-me-maybe

## Description

**call-me-maybe** turns a natural language request into a function call in JSON.

For the prompt `"What is the sum of 2 and 3?"`, the program does not answer `5`. It returns the function to call and its arguments:

```json
{
    "prompt": "What is the sum of 2 and 3?",
    "name": "fn_add_numbers",
    "parameters": {"a": 2.0, "b": 3.0}
}
```

The program uses a small model, **Qwen/Qwen3-0.6B**. Small models are bad at writing valid JSON on their own. To fix this, the program uses **constrained decoding**: at each step, it only lets the model pick tokens that keep the output valid and compliant with the function schema. The output is always valid JSON.

## Instructions

### Requirements

- Python 3.14 or later
- [uv](https://docs.astral.sh/uv/)

### Installation

```bash
make install        # same as: uv sync
```

### Run

```bash
make run            # same as: uv run python -m src
```

By default, the program reads:

- `data/input/function_definitions.json` (available functions)
- `data/input/function_calling_tests.json` (prompts)

and writes the result to `data/output/function_calls.json`.

### Options

```
uv run python -m src [--function-definitions <file>] [--input <file>] [--output <file>] [--generation-visualization]
```

| Option | Description |
|---|---|
| `--function-definitions` | JSON file with the function definitions |
| `--input` | JSON file with the prompts |
| `--output` | JSON file where results are saved |
| `--generation-visualization` | Show each token live, with colors |

### Makefile rules

| Rule | Description |
|---|---|
| `install` | Install the dependencies with uv |
| `run` | Run the program with the default files |
| `run-nested` | Run the program with nested arguments (objects, arrays) |
| `run-visualize` | Run with the generation visualization |
| `run-nested-visualize` | Nested arguments + visualization |
| `debug` | Run the program in debug mode with pdb |
| `test` | Run the tests with coverage |
| `lint` | Run `flake8` and `mypy` |
| `clean` | Remove caches (`__pycache__`, `.mypy_cache`, ...) |
| `help` | Show the program help |

## Example usage

Default files:

```bash
uv run python -m src
```

Custom files:

```bash
uv run python -m src \
    --function-definitions data/input/function_definitions.json \
    --input data/input/function_calling_tests.json \
    --output data/output/function_calls.json
```

Nested arguments, with the visualization:

```bash
uv run python -m src --generation-visualization \
    --function-definitions data/input/nested_function_definitions.json \
    --input data/input/nested_function_calling_tests.json \
    --output data/output/nested_function_calls.json
```

Example of output:

```json
[
    {
        "prompt": "Greet shrek",
        "name": "fn_greet",
        "parameters": {"name": "shrek"}
    },
    {
        "prompt": "Reverse the string 'hello'",
        "name": "fn_reverse_string",
        "parameters": {"s": "hello"}
    }
]
```

If a prompt fails (for example, too many tokens), its entry contains an `error` key instead of `name` and `parameters`. The program keeps going with the next prompts.

## Algorithm explanation

### 1. A finite-state machine (FSM) built from the schema

At startup, the program reads the function definitions and builds an FSM: a table of transitions `(state, character) -> next state`.

- **Function names** are stored as a tree of characters (a trie). Names that share a start (`fn_g...`) share the same states.
- **Fixed text** (`","parameters":{`, keys like `"a":`, commas, braces) is a simple chain of states.
- **Values** have their own small automaton, based on their type:

| Type | Accepted text |
|---|---|
| `string` | `"..."`, with escapes (`\"`, `\\`, `\n`, ...) |
| `integer` | `-12`, `42` |
| `number` | `2.0`, `-3.14` (a decimal part is required) |
| `boolean` | `true`, `false` |
| `null` | `null` |
| `object` | `{` + each property in order + `}` (recursive) |
| `array` | `[` + item, `,` item, ... + `]` (recursive) |

To keep the table small, some transitions use **character groups** instead of single characters: `CHAR` (any character allowed in a string), `DIGIT` (`0-9`) and `SPECIAL_CHAR` (characters allowed after `\`).

The last `}` leads to the `ACCEPT` state: the function call is complete.

### 2. The generation loop

For each prompt:

1. Build a chat prompt (Qwen format) with the list of functions and the user request.
2. Add the start of the answer: `{"prompt":"<the prompt>","name":"`. This part is known, so the model does not write it.
3. Repeat until the FSM reaches `ACCEPT`:
   1. **Forced text**: if the current state has only one possible next character (for example after a key name), the program adds this text directly, without asking the model.
   2. **Logits**: ask the model for the scores of all tokens (`get_logits_from_input_ids`).
   3. **Filtering**: go through the tokens from the best score to the worst. For each token, feed its characters to the FSM one by one. The first token that never reaches an `error` state is chosen. This is the same as setting all invalid tokens to `-inf` and taking the best one.
   4. Add the token to the input and move the FSM to its new state.

Since every chosen token is accepted by the FSM, the final text is always valid JSON that follows the schema.

### 3. Vocabulary

The vocabulary (`token id -> text`) is built once at startup. The FSM works on characters, but the model works on tokens of several characters. Going through each character of a token connects the two.

## Design decisions

- **Character-level FSM**: it is simple, easy to test and it works with any tokenizer. A token is valid if all its characters are valid.
- **Fixed key order**: keys are written in the same order as in the definition file. So all the keys and the JSON punctuation are forced, and the model only has to write the function name and the values.
- **Forced text is added without calling the model**: this saves time and avoids mistakes on parts that are already known.
- **The model picks the function name**: no rule or keyword search. Forced text is disabled inside names, so the choice is always made by the model.
- **Greedy decoding**: the best valid token is always taken. Results are the same on every run.
- **Token limit**: each prompt can use at most 80 generated tokens. This stops a string that never ends. The prompt then gets an error entry instead of crashing the program.
- **Pydantic everywhere**: input files, function definitions and main classes are Pydantic models. Bad files are rejected with a clear message.
- **Clean errors**: missing files, invalid JSON, wrong schemas, unsupported types and `Ctrl+C` all end with a short message, never with a stack trace.

## Performance analysis

- **Accuracy**: on the provided test file, 11/11 prompts call the right function with the right argument types. Values are correct for 10/11: for "Substitute the word 'cat' with 'dog'", the model writes the regex `/cat/g` instead of `cat`. Small models sometimes make mistakes on values, but the FSM makes sure the type is always correct.
- **Reliability**: 100% of the outputs are valid JSON and follow the schema, because invalid tokens can never be picked.
- **Speed**: a large part of the output (keys, quotes, braces, commas) is forced, so the model is only called for the function name and the values. All test prompts run in under the 5-minute limit.

## Challenges faced

- **Tokens vs characters**: a token can contain several characters, like `":"` or `ello`. Solution: run every character of the token through the FSM and only accept the token if all of them pass.
- **Strings with special characters**: a quote or a backslash inside a string can break the JSON. Solution: separate states for strings and escapes, with the `CHAR` and `SPECIAL_CHAR` groups.
- **Numbers**: the subject expects `2.0` for a `number`, not `2`. Solution: the `number` automaton requires a decimal part. `integer` is a separate type.
- **Never-ending generation**: sometimes the model kept writing inside a string. Solution: a limit of 80 tokens per prompt, with an error entry in the output.
- **Nested arguments**: objects and arrays can contain other objects and arrays. Solution: each value gets a unique path (`fn.order.items[]`) used to name its states, and the builders call each other recursively.

## Testing strategy

- **Unit tests with pytest** in `tests/` (run them with `make test`):
  - `test_json_fsm.py`: FSM transitions for every type (strings with escapes, numbers, booleans, null, objects, arrays) and refused inputs.
  - `test_constrained_decoder.py`: choice of the best valid token and forced text, with a mocked model.
  - `test_func_definitions.py`: schema validation (`items` only for arrays, `properties` only for objects, unknown keys).
  - `test_validation.py`: missing files and invalid JSON.
  - `test_main.py`: the generation loop and the token limit, with a mocked model.
- **Coverage**: about 86% of `src/` (the SDK is excluded).
- **Manual tests**: runs on the default and nested files, with edge cases (empty strings, big numbers, special characters, wrong types, missing files, invalid JSON).
- **Static checks**: `make lint` (flake8 + mypy).

## Bonus

- Support for complex nested function arguments (`object`, `array`, `null`, `integer`)
- Visualization of the generation process (`--generation-visualization`): forced tokens and generated tokens are shown with different colors
- Comprehensive test suite

## Resources

### References

- [argparse documentation](https://docs.python.org/3/library/argparse.html)
- [OpenAI Function Calling (video)](https://www.youtube.com/watch?v=aqdWSYWC_LI)
- Constrained decoding: google (A bit of every resources I could find)
- [Qwen concepts: chat model and control tokens](https://qwen.readthedocs.io/en/latest/getting_started/concepts.html)
- [Byte-Pair Encoding tokenizer (video)](https://www.youtube.com/watch?v=zduSFxRajkE&list=PLAqhIrjkxbuWI23v9cThsA9GvCAUhRvKZ&index=9)
- [Finite-State Machines (Stanford CS123)](https://web.stanford.edu/class/cs123/lectures/CS123_lec07_Finite_State_Machine.pdf)
- [JSON Schema: types](https://json-schema.org/understanding-json-schema/reference/type) and [numbers](https://json-schema.org/understanding-json-schema/reference/numeric)
- [Pydantic basics (video)](https://www.youtube.com/watch?v=XIdQ6gO3Anc), [TypeAdapter](https://pydantic.dev/docs/validation/dev/concepts/type_adapter/), [ConfigDict](https://pydantic.dev/docs/validation/latest/api/pydantic/config/)
- [uv: project dependencies](https://docs.astral.sh/uv/concepts/projects/dependencies/#project-dependencies)
- [pytest (video)](https://www.youtube.com/watch?v=EgpLj86ZHFQ), [good practices](https://docs.pytest.org/en/7.1.x/explanation/goodpractices.html), [pytest-cov](https://pytest-cov.readthedocs.io/en/latest/config.html), [pytest-mock](https://pytest-mock.readthedocs.io/en/latest/usage.html)

### AI usage

AI (LLMs) was used:

- to ask specific questions and get a deeper understanding of some topics;
- for repetitive tasks I have already mastered and understood;
