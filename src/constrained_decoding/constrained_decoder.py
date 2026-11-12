from llm_sdk.llm_sdk import Small_LLM_Model
from src.constrained_decoding.json_pda import JSONPushdownAutomaton


class ConstrainedDecoder:
    def __init__(self, model: Small_LLM_Model, pda: JSONPushdownAutomaton):
        self.model: Small_LLM_Model = model
        self.pda: JSONPushdownAutomaton = pda

    def decode(self, logits: list[float]) -> dict[int, str]:
        candidate_transitions: dict[int, str] = {}
        for logit_idx, _ in enumerate(logits):
            if logit_idx >= 151643:
                logits[logit_idx] = float('-inf')
                continue
            token = self.model.decode([logit_idx])
            state_copy = self.pda.get_state()
            for char in token:
                state = self.pda.transition(char)
                if state == "error":
                    logits[logit_idx] = float('-inf')
                    break
            if state != "error":
                candidate_transitions[logit_idx] = state
            self.pda.set_state(state_copy)

        return candidate_transitions
