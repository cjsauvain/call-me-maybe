from src.constrained_decoding.pda_transition_builder import (
    build_transition_table
)


class JSONPushdownAutomaton:
    def __init__(self, func_definitions_path: str):
        self._state: str = ""
        self._transition_table: dict[tuple[str, str], str] = \
            build_transition_table(func_definitions_path)

    def set_state(self, state: str):
        self._state = state

    def get_state(self) -> str:
        return self._state
    
    def get_transition_table(self) -> dict[tuple[str, str], str]:
        return self._transition_table

    def transition(self, char: str) -> str:
        input_category = self._get_input_category(char)
        new_state = self._transition_table.get((self._state, input_category))
        if new_state is None:
            return "error"
        self._state = new_state
        return self._state

    def _get_input_category(self, char: str) -> str:
        if self._is_special_character(char) \
                and self._transition_table.get((self._state, "SPECIAL_CHAR")):
            return "SPECIAL_CHAR"
        elif self._is_digit(char) \
                and self._transition_table.get((self._state, "DIGIT")):
            return "DIGIT"
        elif self._is_character(char) \
                and self._transition_table.get((self._state, "CHAR")):
            return "CHAR"
        return char

    def _is_character(self, char: str) -> bool:
        return ord(char) >= 0x20 and ord(char) != 0x7F and char not in "\"\\"

    def _is_special_character(self, char: str) -> bool:
        return char in '"\\/bfnrt'

    def _is_digit(self, char: str) -> bool:
        return ord(char) >= 0x30 and ord(char) <= 0x39
