from src.constrained_decoding.pda_transition_builder import (
    build_transition_table
)


class JSONPushdownAutomaton:
    def __init__(self, func_definitions_path: str):
        self._state: str = "FUNC_NAME"
        self._transition_table: dict[str, dict] = build_transition_table(
            func_definitions_path
        )
        self._transition_category: str = self._state

    def set_state(self, state: str):
        self._state = state

    def get_state(self) -> str:
        return self._state

    def set_transition_category(self, category: str):
        self._transition_category = category

    def get_transition_category(self) -> str:
        return self._transition_category

    def get_category_transition_table(self) -> dict:
        return self._transition_table[self._transition_category]

    def transition(self, char: str) -> str:
        input_category = self._get_input_category(char)
        new_state = self._transition_table[self._transition_category].get(
            (self._state, input_category)
        )
        if new_state is None:
            return "error"
        self._state = new_state
        return self._state

    def _get_input_category(self, char: str) -> str:
        if self._is_special_character(char) and "ESC" in self._state:
            return "SPECIAL_CHAR"
        elif ("NB_" in self._state or self._state.endswith("\":")) \
                and self._is_digit(char):
            return "DIGIT"
        elif "STR_" in self._state and self._is_character(char):
            return "CHAR"
        return char

    def _is_character(self, char: str) -> bool:
        return ord(char) >= 0x20 and ord(char) != 0x7F and char not in "\"\\"

    def _is_special_character(self, char: str) -> bool:
        return char in '"\\/bfnrt'

    def _is_digit(self, char: str) -> bool:
        return char.isdigit()
