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

    def _get_forced_transition(
            self, current_state: str
    ) -> tuple[bool, str, str]:
        transition_table = self.pda.get_transition_table()
        count = 0
        input_category_tmp = ""
        next_state_tmp = current_state
        for (
            (state, input_category), next_state
         ) in transition_table.items():
            if count > 1:
                return False, "", ""
            if state == current_state:
                count += 1
                input_category_tmp = input_category
                next_state_tmp = next_state
        return count == 1, input_category_tmp, next_state_tmp

    def retrieve_forced_text(self) -> str:
        forced_text = ""
        while True:
            current_state = self.pda.get_state()
            result, input_category, next_state = \
                self._get_forced_transition(current_state)
            if not result:
                break
            if input_category in GENERIC_INPUTS:
                break
            if next_state == "ACCEPT":
                break
            self.pda.set_state(next_state)
            forced_text += input_category
        return forced_text
