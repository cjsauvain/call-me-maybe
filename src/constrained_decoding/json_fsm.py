from src.constrained_decoding.fsm_transition_builder import (
    build_outgoing_transitions,
    build_transition_table
)
from src.function_calling.func_definitions import FuncDefinitions


class JSONSchemaFSM:
    """Finite-state machine accepting valid function calls."""
    def __init__(self, func_definitions: list[FuncDefinitions]):
        """Build the transition tables.

        Args:
            func_definitions: Validated function definitions.
        """
        self._state: str = ""
        self._transition_table: dict[tuple[str, str], str]
        self._func_name_states: set[str]
        self._transition_table, self._func_name_states = \
            build_transition_table(func_definitions)
        self._outgoing_transitions = build_outgoing_transitions(
            self._transition_table
        )

    def is_in_func_name(self, state: str) -> bool:
        """Tell whether a state is inside a function name."""
        return state in self._func_name_states

    def set_state(self, state: str) -> None:
        """Set the current state."""
        self._state = state

    def get_state(self) -> str:
        """Return the current state."""
        return self._state

    def get_unique_outgoing_transition(
        self, state: str
    ) -> tuple[str, str] | None:
        """Return the only transition leaving a state.

        Args:
            state: State to check.

        Returns:
            The (input, next state) pair, or None.
        """
        outgoing_transitions = self._outgoing_transitions.get(state, [])
        if len(outgoing_transitions) != 1:
            return None
        return outgoing_transitions[0]

    def transition(self, char: str) -> str:
        """Read one character and move to the next state.

        Args:
            char: Character to read.

        Returns:
            The new state, or 'error' if refused.
        """
        input_category = self._get_input_category(char)
        new_state = self._transition_table.get((self._state, input_category))
        if new_state is None:
            return "error"
        self._state = new_state
        return self._state

    def _get_input_category(self, char: str) -> str:
        """Find the input matching a character in the current state."""
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
        """Tell whether a character can appear as is in a string."""
        return ord(char) >= 0x20 and ord(char) != 0x7F and char not in "\"\\"

    def _is_special_character(self, char: str) -> bool:
        """Tell whether a character can follow a backslash."""
        return char in '"\\/bfnrt'

    def _is_digit(self, char: str) -> bool:
        """Tell whether a character is an ASCII digit."""
        return ord(char) >= 0x30 and ord(char) <= 0x39
