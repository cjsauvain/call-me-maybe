from typing import Callable

from src.function_calling.func_definitions import FuncDefinitions, ParamModel


ArgBuilderType = Callable[
    [dict[tuple[str, str], str], ParamModel, str, str],
    str
]


def _add_new_entry(
    transition_table: dict[tuple[str, str], str],
    state: str, char: str
) -> str:
    """Add a transition to a new state.

    Args:
        transition_table: Table to fill.
        state: Source state.
        char: Character read.

    Returns:
        The new state.
    """
    new_state = f"{state}{char}"
    transition_table[(state, char)] = new_state
    return new_state


def _build_key_transitions(
        transition_table: dict[tuple[str, str], str],
        state: str, key: str,
        visited_states: set[str] | None = None
) -> str:
    """Add transitions reading a text.

    Args:
        transition_table: Table to fill.
        state: State to start from.
        key: Text to read.
        visited_states: If given, collects the states reached.

    Returns:
        The state after the text.
    """
    for char in key:
        if not transition_table.get((state, char)):
            state = _add_new_entry(transition_table, state, char)
        else:
            state = transition_table[(state, char)]
        if visited_states is not None:
            visited_states.add(state)
    return state


def _build_func_name_transitions(
    transition_table: dict[tuple[str, str], str],
    func_name_states: set[str],
    func_name: str
) -> str:
    """Add transitions for a function name and the `","parameters":{`
    text after it.

    Args:
        transition_table: Table to fill.
        func_name_states: Collects the states inside the name.
        func_name: Name of the function.

    Returns:
        The state where the parameters start.
    """
    state = ""
    func_name_states.add(state)
    state = _build_key_transitions(
        transition_table, state,
        func_name, func_name_states
    )
    state = _build_key_transitions(
        transition_table, state,
        '","parameters":{'
    )
    return state


def _build_key(
    transition_table: dict[tuple[str, str], str],
    state: str, key_name: str
) -> str:
    """Add transitions for a JSON key and its colon.

    Args:
        transition_table: Table to fill.
        state: State to start from.
        key_name: Name of the key.

    Returns:
        The state after the colon.
    """
    return _build_key_transitions(
        transition_table, state,
        "\"" + key_name + "\":"
    )


def _build_arg_string_transitions(
        transition_table: dict[tuple[str, str], str],
        _: ParamModel, path: str, state: str
) -> str:
    """Add transitions for a JSON string.

    Args:
        transition_table: Table to fill.
        _: Unused, keeps a common signature.
        path: Unique path of the value.
        state: State to start from.

    Returns:
        The state after the value.
    """
    transition_table[(state, "\"")] = f"STR_{path}"
    transition_table[(f"STR_{path}", "\\")] = f"ESC_{path}"
    transition_table[(f"STR_{path}", "CHAR")] = f"STR_{path}"
    transition_table[(f"ESC_{path}", "SPECIAL_CHAR")] = f"STR_{path}"
    transition_table[(f"STR_{path}", "\"")] = f"EXPECT_SEPARATOR_{path}"

    return f"EXPECT_SEPARATOR_{path}"


def _build_arg_integer_transitions(
        transition_table: dict[tuple[str, str], str],
        _: ParamModel, path: str, state: str
) -> str:
    """Add transitions for a JSON integer.

    Args:
        transition_table: Table to fill.
        _: Unused, keeps a common signature.
        path: Unique path of the value.
        state: State to start from.

    Returns:
        The state after the value.
    """
    transition_table[(state, "-")] = f"WAIT_NB_{path}"
    transition_table[(state, "DIGIT")] = f"NB_{path}"
    transition_table[(f"WAIT_NB_{path}", "DIGIT")] = f"NB_{path}"
    transition_table[(f"NB_{path}", "DIGIT")] = f"NB_{path}"

    return f"NB_{path}"


def _build_arg_number_transitions(
        transition_table: dict[tuple[str, str], str],
        _: ParamModel, path: str, state: str
) -> str:
    """Add transitions for a JSON number with decimals.

    Args:
        transition_table: Table to fill.
        _: Unused, keeps a common signature.
        path: Unique path of the value.
        state: State to start from.

    Returns:
        The state after the value.
    """
    transition_table[(state, "-")] = f"WAIT_NB_{path}"
    transition_table[(state, "DIGIT")] = f"NB_{path}"
    transition_table[(f"WAIT_NB_{path}", "DIGIT")] = f"NB_{path}"
    transition_table[(f"NB_{path}", "DIGIT")] = f"NB_{path}"
    transition_table[(f"NB_{path}", ".")] = f"WAIT_NB_DECIMAL_{path}"
    transition_table[(f"NB_DECIMAL_{path}", "DIGIT")] = f"NB_DECIMAL_{path}"
    transition_table[(f"WAIT_NB_DECIMAL_{path}", "DIGIT")] = \
        f"NB_DECIMAL_{path}"

    return f"NB_DECIMAL_{path}"


def _build_arg_boolean_transitions(
        transition_table: dict[tuple[str, str], str],
        _: ParamModel, path: str, state: str
) -> str:
    """Add transitions for `true` and `false`.

    Args:
        transition_table: Table to fill.
        _: Unused, keeps a common signature.
        path: Unique path of the value.
        state: State to start from.

    Returns:
        The state after the value.
    """
    transition_table[(state, "t")] = f"BOOL_T_{path}"
    transition_table[(f"BOOL_T_{path}", "r")] = f"BOOL_R_{path}"
    transition_table[(f"BOOL_R_{path}", "u")] = f"BOOL_U_{path}"
    transition_table[(f"BOOL_U_{path}", "e")] = f"EXPECT_SEPARATOR_{path}"
    transition_table[(state, "f")] = f"BOOL_F_{path}"
    transition_table[(f"BOOL_F_{path}", "a")] = f"BOOL_A_{path}"
    transition_table[(f"BOOL_A_{path}", "l")] = f"BOOL_L_{path}"
    transition_table[(f"BOOL_L_{path}", "s")] = f"BOOL_S_{path}"
    transition_table[(f"BOOL_S_{path}", "e")] = f"EXPECT_SEPARATOR_{path}"

    return f"EXPECT_SEPARATOR_{path}"


def _build_arg_null_transitions(
        transition_table: dict[tuple[str, str], str],
        _: ParamModel, path: str, state: str
) -> str:
    """Add transitions for `null`.

    Args:
        transition_table: Table to fill.
        _: Unused, keeps a common signature.
        path: Unique path of the value.
        state: State to start from.

    Returns:
        The state after the value.
    """
    transition_table[(state, "n")] = f"NULL_N_{path}"
    transition_table[(f"NULL_N_{path}", "u")] = f"NULL_U_{path}"
    transition_table[(f"NULL_U_{path}", "l")] = f"NULL_L_{path}"
    transition_table[(f"NULL_L_{path}", "l")] = f"EXPECT_SEPARATOR_{path}"

    return f"EXPECT_SEPARATOR_{path}"


def _build_arg_object_transitions(
        transition_table: dict[tuple[str, str], str],
        arg_schema: ParamModel, path: str, state: str
) -> str:
    """Add transitions for a JSON object.

    Args:
        transition_table: Table to fill.
        arg_schema: Schema of the object.
        path: Unique path of the value.
        state: State to start from.

    Returns:
        The state after the value.

    Raises:
        ValueError: If the object has no properties.
    """
    new_state = f"{state}{{"
    transition_table[(state, "{")] = new_state
    state = new_state
    properties = arg_schema.properties
    if properties is None:
        raise ValueError(f"Object parameter `{path}` has no properties.")
    args_nb = len(properties)
    arg = ""
    for arg in properties:
        state = _build_key(transition_table, state, arg)
        state = _build_arg_transitions(
            transition_table, properties[arg],
            f"{path}.{arg}", state)
        args_nb -= 1
        separator = "}" if args_nb == 0 else ","
        transition_table[(state, separator)] = f"END_{path}.{arg}"
        state = f"END_{path}.{arg}"

    return f"END_{path}.{arg}"


def _build_arg_array_transitions(
        transition_table: dict[tuple[str, str], str],
        arg_schema: ParamModel, path: str, state: str
) -> str:
    """Add transitions for a JSON array.

    Args:
        transition_table: Table to fill.
        arg_schema: Schema of the array.
        path: Unique path of the value.
        state: State to start from.

    Returns:
        The state after the value.

    Raises:
        ValueError: If the array has no items.
    """
    new_state = f"{state}["
    transition_table[(state, "[")] = new_state
    state = new_state
    items = arg_schema.items
    if items is None:
        raise ValueError(f"Array parameter {path} has no items.")
    next_state = f"NEXT_{path}"
    end_state = f"ARR_END_{path}"
    state = _build_arg_transitions(transition_table, items, f"{path}[]", state)
    _build_arg_transitions(transition_table, items, f"{path}[]", next_state)
    transition_table[(state, ",")] = next_state
    transition_table[(state, "]")] = end_state

    return end_state


ARG_TYPE_TO_BUILDER: dict[
    str,
    ArgBuilderType
] = {
    "string": _build_arg_string_transitions,
    "integer": _build_arg_integer_transitions,
    "number": _build_arg_number_transitions,
    "boolean": _build_arg_boolean_transitions,
    "null": _build_arg_null_transitions,
    "object": _build_arg_object_transitions,
    "array": _build_arg_array_transitions
}


def _build_arg_transitions(
        transition_table: dict[tuple[str, str], str],
        arg_schema: ParamModel, path: str, state: str
) -> str:
    """Call the builder matching the type of the value.

    Args:
        transition_table: Table to fill.
        arg_schema: Schema of the value.
        path: Unique path of the value.
        state: State to start from.

    Returns:
        The state after the value.

    Raises:
        ValueError: If the type is not supported.
    """
    arg_type: str = arg_schema.type
    builder: ArgBuilderType | None = ARG_TYPE_TO_BUILDER.get(arg_type, None)
    if not builder:
        raise ValueError(
            f"Type `{arg_type}` is not supported. "
            "Supported types are: string, integer, number,"
            " boolean, null, object, array."
        )
    return builder(
            transition_table,
            arg_schema, path, state
    )


def _build_func_params_transitions(
    transition_table: dict[tuple[str, str], str],
    func_params: dict[str, ParamModel], func_name: str,
    state: str
) -> None:
    """Add transitions for the parameters of a function.

    Also adds the two closing braces, the last one leading to ACCEPT.

    Args:
        transition_table: Table to fill.
        func_params: Schema of each parameter.
        func_name: Name of the function.
        state: State where the parameters start.
    """
    len_fun_params = len(func_params)
    for arg in func_params:
        path = f"{func_name}.{arg}"
        state = _build_key(transition_table, state, arg)
        state = _build_arg_transitions(
            transition_table,
            func_params[arg], path, state
        )
        len_fun_params -= 1
        if len_fun_params > 0:
            transition_table[(state, ",")] = f"END_{path}"
            state = f"END_{path}"
    transition_table[(state, "}")] = f"END_{func_name}}}"
    transition_table[(f"END_{func_name}}}", "}")] = "ACCEPT"


def _build_func_transitions(
    transition_table: dict[tuple[str, str], str],
    func_name_states: set[str],
    func: dict
) -> None:
    """Add transitions for a whole function call.

    Args:
        transition_table: Table to fill.
        func_name_states: Collects the states inside the name.
        func: Name and parameters of the function.
    """
    state = _build_func_name_transitions(
        transition_table, func_name_states, func["name"]
    )
    _build_func_params_transitions(
        transition_table,
        func["parameters"],
        func["name"],
        state
    )


def build_transition_table(
    func_definitions: list[FuncDefinitions]
) -> tuple[dict[tuple[str, str], str], set[str]]:
    """Build the automaton of all the function calls.

    Args:
        func_definitions: Validated function definitions.

    Returns:
        The transition table and the states inside names.
    """
    transition_table: dict[tuple[str, str], str] = {}
    func_name_states: set[str] = set()
    for func_definition in func_definitions:
        func = {
            "name": func_definition.name,
            "parameters": func_definition.parameters
        }
        _build_func_transitions(transition_table, func_name_states, func)
    return transition_table, func_name_states


def build_outgoing_transitions(
    transition_table: dict[tuple[str, str], str]
) -> dict[str, list[tuple[str, str]]]:
    """Group the transitions by source state.

    Args:
        transition_table: Table to group.

    Returns:
        The (input, next state) pairs leaving each state.
    """
    outgoing_transitions: dict[str, list[tuple[str, str]]] = {}

    for (state, input_category), next_state in transition_table.items():
        outgoing_transitions.setdefault(
            state, []
        ).append((input_category, next_state))

    return outgoing_transitions
