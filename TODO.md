- Rename Pushdown Automaton as Finite-State Machine
- Refactor to eliminate code duplication.
- Error handling
- Remove debug prints
- Remove comments

## Subject compliance (mandatory part)

### Blocking
- [x] Accept `"integer"` in `ParamTypeName` (src/function_calling/param_types.py): the private set currently fails input validation
- [x] Make mypy pass with the subject flags (`make lint`): 14 errors, mostly missing return types and the untyped `indexes_to_ignore`
- [ ] Never crash: handle the `RuntimeError("No valid token found")` from `_generate_tokens` (mark the prompt as failed instead of stopping the whole run)
- [ ] Never crash: wrap `save_llm_output` (json.loads + file write) in try/except with a clear message
- [ ] Never crash: handle errors while loading the model (`Small_LLM_Model()`)
- [ ] Add PEP 257 docstrings to every function and class (48 missing)
- [ ] Use pydantic for every class: `GenerationState`, `JSONPushdownAutomaton`, `ConstrainedDecoder`

### To fix or check
- [x] Makefile `clean`: also remove `.mypy_cache`
- [x] Makefile `run`: use `uv run python -m src` and do not depend on `.env` (it will not exist on the reviewer's machine)
- [ ] Output objects must contain exactly `prompt`, `name`, `parameters`: decide how to report failed prompts without the extra `error` key
- [ ] Remove the `accelerate` dependency if unused (Hugging Face packages are forbidden)
- [ ] Add `numpy` to the dependencies (requested by the subject alongside pydantic)

### README.md (in English)
- [ ] First line in italics: *This project has been created as part of the 42 curriculum by <login>*
- [ ] Description section
- [ ] Instructions section (installation and execution)
- [ ] Resources section, including how AI was used (for which tasks and which parts of the project)
- [ ] Algorithm explanation (constrained decoding approach)
- [ ] Design decisions
- [ ] Performance analysis (accuracy, speed, reliability)
- [ ] Challenges faced and how they were solved
- [ ] Testing strategy
- [ ] Example usage