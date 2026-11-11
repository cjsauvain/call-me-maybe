from llm_sdk.llm_sdk import Small_LLM_Model
from src.constrained_decoding.json_pda import JSONPushdownAutomaton


class ConstrainedDecoder:
    def __init__(self, model: Small_LLM_Model, pda: JSONPushdownAutomaton):
        self.model: Small_LLM_Model = model
        self.pda: JSONPushdownAutomaton = pda

    def decode(self, logits: list[float]) -> dict[int, tuple[str, list]]:
        candidate_transitions: dict[int, tuple[str, list]] = {}
        for logit_idx, _ in enumerate(logits):
            token = self.model.decode([logit_idx])
            state_copy, stack_copy = (
                self.pda.get_state(),
                self.pda.get_stack_copy()
            )
            for char in token:
                status = self.pda.transition(char)
                if status == "error":
                    logits[logit_idx] = float('-inf')
                    break
            if status != "error":
                candidate_transitions[logit_idx] = (
                    self.pda.get_state(),
                    self.pda.get_stack()
                )
            self.pda.set_state(state_copy)
            self.pda.set_stack(stack_copy)

        return candidate_transitions
