from llm_sdk.llm_sdk import Small_LLM_Model
from src.constrained_decoding.json_fsm import JSONSchemaFSM


VOCAB_SIZE = 151643
GENERIC_INPUTS = {"CHAR", "SPECIAL_CHAR", "DIGIT"}


class ConstrainedDecoder:
    """Pick the next token using the model logits and the FSM.

    Attributes:
        model: The language model.
        fsm: Automaton checking the output.
        vocab: Text of each token id.
    """
    def __init__(self, model: Small_LLM_Model, fsm: JSONSchemaFSM):
        """Build the token vocabulary.

        Args:
            model: The language model.
            fsm: Automaton checking the output.
        """
        self.model: Small_LLM_Model = model
        self.fsm: JSONSchemaFSM = fsm
        self.vocab: list[str] = [model.decode([i]) for i in range(VOCAB_SIZE)]

    def decode(self, logits: list[float]) -> tuple[int, str] | None:
        """Pick the most likely token accepted by the FSM.

        Args:
            logits: Score of each token.

        Returns:
            The token id and its FSM state, or None.
        """
        sorted_logits = sorted(
            range(len(logits)), key=logits.__getitem__, reverse=True
        )
        state_copy = self.fsm.get_state()
        for token_id in sorted_logits:
            if token_id >= VOCAB_SIZE:
                continue
            token = self.vocab[token_id]
            if not token:
                continue
            state = state_copy
            for char in token:
                state = self.fsm.transition(char)
                if state == "error":
                    break
            self.fsm.set_state(state_copy)
            if state != "error":
                return token_id, state
        return None

    def retrieve_forced_text(self) -> str:
        """Follow the transitions forced by the FSM.

        Returns:
            The forced text, empty if nothing is forced.
        """
        forced_text = ""
        while True:
            current_state = self.fsm.get_state()
            result = self.fsm.get_unique_outgoing_transition(current_state)
            if result is None:
                break
            input_category, next_state = result
            if input_category in GENERIC_INPUTS or next_state == "ACCEPT":
                break
            self.fsm.set_state(next_state)
            forced_text += input_category
        return forced_text
