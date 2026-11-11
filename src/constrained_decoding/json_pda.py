import json


def _add_new_entry(any_transition_table: dict, state: str, char: str) -> str:
    new_state = f"{state}_{char}"
    any_transition_table[(state, char)] = new_state
    return new_state


def _build_func_name_transitions(transition_table: dict, func_name: str):
    state = "FUNC_NAME"
    for char in func_name:
        if not transition_table["FUNC_NAME"].get((state), char):
            state = _add_new_entry(
                transition_table["FUNC_NAME"],
                state, char
            )
    transition_table["FUNC_NAME"][(state, "\"")] = "ACCEPT"


def _build_arg_object_string_transitions(
        func_params_transition_table: dict,
        arg_name: str, args_nb: int,
        state: str
) -> str:
    pass


def _build_arg_string_transitions(
        func_params_transition_table: dict,
        arg_name: str, args_nb: int,
        state: str
) -> str:
    json_start = "\"" + arg_name + "\":"
    for char in json_start:
        if func_params_transition_table.get((state, char)) is None:
            state = _add_new_entry(
                func_params_transition_table,
                arg_name, char
            )

    func_params_transition_table[(state, "\"")] = f"STR_{arg_name}"
    func_params_transition_table[(f"STR_{arg_name}", "\\")] = \
        f"ESCAPED_{arg_name}"
    func_params_transition_table[(f"STR_{arg_name}", "ANY_CHAR")] = \
        f"STR_{arg_name}"
    func_params_transition_table[(f"ESCAPED_{arg_name}", "SPECIAL_CHAR")] = \
        f"STR_{arg_name}"

    if args_nb > 1:
        final_state = f"END_{arg_name}"
        func_params_transition_table[(f"STR_{arg_name}", "\"")] = \
            f"EXPECT_COMMA_{arg_name}"
        func_params_transition_table[(f"EXPECT_COMMA_{arg_name}", ",")] = \
            final_state
        return final_state
    final_state = "ACCEPT"
    func_params_transition_table[(f"STR_{arg_name}", "\"")] = \
        f"QUOTE_{arg_name}"
    func_params_transition_table[(f"QUOTE_{arg_name}", "}")] = final_state
    return final_state


def _build_arg_object_number_transitions(
        func_params_transition_table: dict,
        arg_name: str, args_nb: int,
        state: str
) -> str:
    pass


def _build_arg_number_transitions(
        func_params_transition_table: dict,
        arg_name: str, args_nb: int,
        state: str
) -> str:
    json_start = "\"" + arg_name + "\":"
    for char in json_start:
        if func_params_transition_table.get((state, char)) is None:
            state = _add_new_entry(
                func_params_transition_table,
                arg_name, char
            )

    func_params_transition_table[(state, "-")] = \
        f"NB_{arg_name}"
    func_params_transition_table[(state, "ANY_DIGIT")] = \
        f"NB_{arg_name}"
    func_params_transition_table[(f"NB_{arg_name}", "ANY_DIGIT")] = \
        f"NB_{arg_name}"
    func_params_transition_table[(f"NB_{arg_name}", ".")] = \
        f"NB_DECIMAL_{arg_name}"
    func_params_transition_table[(f"NB_DECIMAL_{arg_name}", "ANY_DIGIT")] = \
        f"NB_DECIMAL_{arg_name}"

    if args_nb > 1:
        final_state = f"END_{arg_name}"
        func_params_transition_table[(f"NB_{arg_name}", ",")] = final_state
        func_params_transition_table[(f"NB_DECIMAL_{arg_name}", ",")] = \
            final_state
        return final_state
    final_state = "ACCEPT"
    func_params_transition_table[(f"NB_{arg_name}", "}")] = final_state
    func_params_transition_table[(f"NB_DECIMAL_{arg_name}", "}")] = final_state
    return final_state


def _build_arg_object_boolean_transitions(
        func_params_transition_table: dict,
        arg_name: str, args_nb: int,
        state: str
) -> str:
    pass


def _build_arg_boolean_transitions(
        func_params_transition_table: dict,
        arg_name: str, args_nb: int,
        state: str
) -> str:
    json_start = "\"" + arg_name + "\":"
    for char in json_start:
        if func_params_transition_table.get((state, char)) is None:
            state = _add_new_entry(
                func_params_transition_table,
                arg_name, char
            )

    func_params_transition_table[(state, "t")] = \
        f"BOOL_T_{arg_name}"
    func_params_transition_table[(f"BOOL_T_{arg_name}", "r")] = \
        f"BOOL_R_{arg_name}"
    func_params_transition_table[(f"BOOL_R_{arg_name}", "u")] = \
        f"BOOL_U_{arg_name}"
    func_params_transition_table[(f"BOOL_U_{arg_name}", "e")] = \
        f"BOOL_E_{arg_name}"
    func_params_transition_table[(f"BOOL_E_{arg_name}", ",")] = \
        f"END_{arg_name}"
    func_params_transition_table[(state, "f")] = \
        f"BOOL_F_{arg_name}"
    func_params_transition_table[(f"BOOL_F_{arg_name}", "a")] = \
        f"BOOL_A_{arg_name}"
    func_params_transition_table[(f"BOOL_A_{arg_name}", "l")] = \
        f"BOOL_L_{arg_name}"
    func_params_transition_table[(f"BOOL_L_{arg_name}", "s")] = \
        f"BOOL_S_{arg_name}"
    func_params_transition_table[(f"BOOL_S_{arg_name}", "e")] = \
        f"BOOL_E_{arg_name}"

    if args_nb > 1:
        final_state = f"END_{arg_name}"
        func_params_transition_table[(f"BOOL_E_{arg_name}", ",")] = final_state
        return final_state
    final_state = "ACCEPT"
    func_params_transition_table[(f"BOOL_E_{arg_name}", "}")] = final_state
    return final_state


def _build_arg_object_null_transitions(
        func_params_transition_table: dict,
        arg_name: str, args_nb: int,
        state: str
) -> str:
    pass


def _build_arg_null_transitions(
        func_params_transition_table: dict,
        arg_name: str, args_nb: int,
        state: str
) -> str:
    json_start = "\"" + arg_name + "\":"
    for char in json_start:
        if func_params_transition_table.get((state, char)) is None:
            state = _add_new_entry(
                func_params_transition_table,
                arg_name, char
            )

    func_params_transition_table[(state, "n")] = \
        f"NULL_N_{arg_name}"
    func_params_transition_table[(f"NULL_N_{arg_name}", "u")] = \
        f"NULL_U_{arg_name}"
    func_params_transition_table[(f"NULL_U_{arg_name}", "l")] = \
        f"NULL_L_{arg_name}"
    func_params_transition_table[(f"NULL_L_{arg_name}", "l")] = \
        f"NULL_L_{arg_name}"

    if args_nb > 1:
        final_state = f"END_{arg_name}"
        func_params_transition_table[(f"NULL_L_{arg_name}", ",")] = final_state
        return final_state
    final_state = "ACCEPT"
    func_params_transition_table[(f"NULL_L_{arg_name}", "}")] = final_state
    return final_state


def _build_arg_object_transitions(
        func_params_transition_table: dict,
        arg_schema: dict, arg_name: str,
        args_nb: int, state: str
) -> str:
    json_start = "\"" + arg_name + "\":{"
    for char in json_start:
        if func_params_transition_table.get((state, char)) is None:
            state = _add_new_entry(
                func_params_transition_table,
                arg_name, char
            )
    if arg_schema["type"] == "object":
        # HOW TO PASS ARG_NAME AND STATE THROUGH RECURSION ????
        return _build_arg_object_transitions(
            func_params_transition_table,
            arg_schema, arg_name,
            f"{args_nb}", state
            # HOW TO PASS ARG_NAME AND STATE THROUGH RECURSION ????
        )
    if arg_schema["type"] == "array":
        return _build_arg_array_transitions(
            func_params_transition_table,
            arg_schema, arg_name,
            f"{args_nb}_[", state
        )
    if arg_schema["type"] == "string":
        return _build_arg_object_string_transitions(
            func_params_transition_table,
            arg_schema, arg_name,
            args_nb, state
        )
    if arg_schema["type"] == "number":
        return _build_arg_object_number_transitions(
            func_params_transition_table,
            arg_schema, arg_name,
            args_nb, state
        )
    if arg_schema["type"] == "boolean":
        return _build_arg_object_boolean_transitions(
            func_params_transition_table,
            arg_schema, arg_name,
            args_nb, state
        )
    if arg_schema["type"] == "null":
        return _build_arg_object_null_transitions(
            func_params_transition_table,
            arg_schema, arg_name,
            args_nb, state
        )
    raise TypeError(
        "This JSON type is not supported."
        "Supported types are: string, number, boolean, null, object, array"
    )


def _build_arg_array_transitions(
        func_params_transition_table: dict,
        arg_schema: dict, arg_name: str,
        args_nb: int, state: str
) -> str:
    json_start = "\"" + arg_name + "\":["
    for char in json_start:
        if func_params_transition_table.get((state, char)) is None:
            state = _add_new_entry(
                func_params_transition_table,
                arg_name, char
            )


def _build_arg_transitions(
        func_params_transition_table: dict,
        arg_schema: dict, arg_name: str,
        args_nb: int, start_state: str
) -> str:
    state = f"START_{arg_name}" if start_state == "START" else start_state
    if arg_schema["type"] == "string":
        return _build_arg_string_transitions(
            func_params_transition_table, arg_name,
            args_nb, state
        )
    if arg_schema["type"] == "number":
        return _build_arg_number_transitions(
            func_params_transition_table, arg_name,
            args_nb, state
        )
    if arg_schema["type"] == "boolean":
        return _build_arg_boolean_transitions(
            func_params_transition_table, arg_name,
            args_nb, state
        )
    if arg_schema["type"] == "null":
        return _build_arg_null_transitions(
            func_params_transition_table, arg_name,
            args_nb, state
        )
    if arg_schema["type"] == "object":
        return _build_arg_object_transitions(
            func_params_transition_table,
            arg_schema, arg_name,
            args_nb, state
        )
    if arg_schema["type"] == "array":
        return _build_arg_array_transitions(
            func_params_transition_table,
            arg_schema, arg_name,
            args_nb, state
        )
    raise TypeError(
        "This JSON type is not supported."
        "Supported types are: string, number, boolean, null, object, array"
    )


def _build_func_params_transitions(
    transition_table: dict,
    func_params: str, func_name: str
):
    transition_table[func_name] = {}
    args_nb = len(func_params)
    state = "START"
    for arg in func_params:
        state = _build_arg_transitions(
            transition_table[func_name],
            func_params[arg], arg, args_nb,
            state
        )
        args_nb -= 1


def _build_func_transitions(transition_table: dict, func: dict):
    _build_func_name_transitions(transition_table, func["name"])
    _build_func_params_transitions(transition_table, func["parameters"])


def _build_transition_table(func_definitions_path: str) -> dict[str, dict]:
    with open(func_definitions_path, "r") as file:
        func_definitions_json = json.load(file)

    transition_table: dict[str, dict] = {}
    for func_definition in func_definitions_json:
        func = {
            "name": func_definition["name"],
            "parameters": func_definition["parameters"]
        }
        _build_func_transitions(transition_table, func)

    return transition_table


class JSONPushdownAutomaton:
    def __init__(self, func_definitions_path: str):
        self._state: str = "FUNC_NAME"
        self._stack: list = self.reset_stack()
        self._transition_table: dict[str, dict] = _build_transition_table(
            func_definitions_path
        )

    def get_state(self) -> str:
        return self._state

    def get_stack(self) -> list:
        return self._stack

    def get_stack_copy(self) -> list:
        return self._stack.copy()

    def set_state(self, state: str):
        self._state = state

    def set_stack(self, stack: list):
        self._stack = stack

    def reset_state(self):
        self._state = "FUNC_NAME"

    def reset_stack(self):
        self._stack = ["{"]

    def commit_transition(self, state, stack):
        self._state = state
        self._stack = stack

    def transition(self, char: str) -> str:
        status = "accept"
        input_category = self._get_input_category(char)

        new_state = self._transition_table.get((self._state, input_category))
        if new_state is None:
            return "error"

        if input_category in "{}[]":
            status = self._update_stack(input_category)
            if status == "error":
                return status

        if new_state == "EXPECT_KEY" \
                and self._stack \
                and self._stack[-1] == "[":
            new_state = "EXPECT_VAL_OR_OBJECT"
        self._state = new_state
        return status

    def _update_stack(self, char: str) -> str:
        status = "accept"
        if char in "{[":
            self._stack.append(char)
        elif char in "}]":
            if not self._stack:
                return "error"
            top_item = self._stack[-1]
            if ord(char) != ord(top_item) + 2:
                return "error"
            self._stack.pop()
            status = status if self._stack else "end"
        return status

    def _get_input_category(self, char: str) -> str:
        input_category = char
        if self._is_any_special_character(char) \
                and self._state == "EXPECT_ESCAPED":
            input_category = "ANY_SPECIAL_CHARACTER"
        elif self._state == "STR_KEY" \
                and self._is_any_character(char) \
                and char not in "!\"#$%&'()*+,-./:;<=>?@\\[]^`{}|~":
            input_category = "ANY_KEY_CHARACTER"
        elif self._state == "STR_VAL" \
                and self._is_any_character(char) \
                and char not in "\"\\":
            input_category = "ANY_STR_VAL_CHARACTER"
        elif self._state == "VAL" \
                and self._is_any_character(char) \
                and char not in " !\"#$%&'()*+,/:;<=>?@\\[]^`{}|~":
            input_category = "ANY_VAL_CHARACTER"
        return input_category

    def _is_any_character(self, char: str) -> bool:
        return ord(char) >= 0x20 and ord(char) != 0x7F

    def _is_any_special_character(self, char: str) -> bool:
        return char in '"\\/bfnrt'
