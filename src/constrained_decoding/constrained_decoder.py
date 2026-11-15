from llm_sdk.llm_sdk import Small_LLM_Model
from src.constrained_decoding.json_pda import JSONPushdownAutomaton


VOCAB_SIZE = 151643
GENERIC_INPUTS = {"CHAR", "SPECIAL_CHAR", "DIGIT"}


class ConstrainedDecoder:
    def __init__(self, model: Small_LLM_Model, pda: JSONPushdownAutomaton):
        self.model: Small_LLM_Model = model
        self.pda: JSONPushdownAutomaton = pda
        self.vocab: list[str] = [model.decode([i]) for i in range(VOCAB_SIZE)]

    def decode(self, logits: list[float]) -> tuple[int, str] | None:
        sorted_logits = sorted(
            range(len(logits)), key=logits.__getitem__, reverse=True
        )
        state_copy = self.pda.get_state()
        for token_id in sorted_logits:
            if token_id >= VOCAB_SIZE:
                continue
            token = self.vocab[token_id]
            if not token:
                continue
            state = state_copy
            for char in token:
                state = self.pda.transition(char)
                if state == "error":
                    break
            self.pda.set_state(state_copy)
            if state != "error":
                return token_id, state
        return None

    def retrieve_forced_text(self) -> str:
        forced_text = ""
        while True:
            current_state = self.pda.get_state()
            result = self.pda.get_unique_outgoing_transition(current_state)
            if result is None:
                break
            input_category, next_state = result
            if input_category in GENERIC_INPUTS or next_state == "ACCEPT":
                break
            self.pda.set_state(next_state)
            forced_text += input_category
        return forced_text
