import json
from typing import Callable

ArgBuilderType = Callable[
    [dict[tuple[str, str], str], dict, str, str, bool],
    str
]


def _add_new_entry(
    transition_table: dict[tuple[str, str], str],
    state: str, char: str
) -> str:
    new_state = f"{state}{char}"
    transition_table[(state, char)] = new_state
    return new_state


def _build_func_name_transitions(
    transition_table: dict[tuple[str, str], str],
    func_name_states: set[str],
    func_name: str
) -> str:
    state = ""
    func_name_states.add(state)
    for char in func_name:
        if not transition_table.get((state, char)):
            state = _add_new_entry(transition_table, state, char)
        else:
            state = transition_table[(state, char)]
        func_name_states.add(state)
    for char in '","parameters":{':
        new_state = state + char
        transition_table[(state, char)] = new_state
        state = new_state
    return state


def _build_key_transitions(
        transition_table: dict[tuple[str, str], str],
        state: str, key: str
) -> str:
    for char in key:
        if not transition_table.get((state, char)):
            state = _add_new_entry(transition_table, state, char)
        else:
            state = transition_table[(state, char)]
    return state


def _build_arg_string_transitions(
        transition_table: dict[tuple[str, str], str],
        _: dict, path: str, state: str,
        add_key: bool = True
) -> str:
    if add_key:
        key_name = path.split(".")[-1]
        state = _build_key_transitions(
            transition_table, state,
            "\"" + key_name + "\":"
        )
    transition_table[(state, "\"")] = f"STR_{path}"
    transition_table[(f"STR_{path}", "\\")] = f"ESC_{path}"
    transition_table[(f"STR_{path}", "CHAR")] = f"STR_{path}"
    transition_table[(f"ESC_{path}", "SPECIAL_CHAR")] = f"STR_{path}"
    transition_table[(f"STR_{path}", "\"")] = f"EXPECT_SEPARATOR_{path}"

    return f"EXPECT_SEPARATOR_{path}"


def _build_arg_integer_transitions(
        transition_table: dict[tuple[str, str], str],
        _: dict, path: str, state: str,
        add_key: bool = True
) -> str:
    if add_key:
        key_name = path.split(".")[-1]
        state = _build_key_transitions(
            transition_table, state,
            "\"" + key_name + "\":"
        )
    transition_table[(state, "-")] = f"WAIT_NB_{path}"
    transition_table[(state, "DIGIT")] = f"NB_{path}"
    transition_table[(f"WAIT_NB_{path}", "DIGIT")] = f"NB_{path}"
    transition_table[(f"NB_{path}", "DIGIT")] = f"NB_{path}"

    return f"NB_{path}"


def _build_arg_number_transitions(
        transition_table: dict[tuple[str, str], str],
        _: dict, path: str, state: str,
        add_key: bool = True
) -> str:
    if add_key:
        key_name = path.split(".")[-1]
        state = _build_key_transitions(
            transition_table, state,
            "\"" + key_name + "\":"
        )
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
        _: dict, path: str, state: str,
        add_key: bool = True
) -> str:
    if add_key:
        key_name = path.split(".")[-1]
        state = _build_key_transitions(
            transition_table, state,
            "\"" + key_name + "\":"
        )
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
        _: dict, path: str, state: str,
        add_key: bool = True
) -> str:
    if add_key:
        key_name = path.split(".")[-1]
        state = _build_key_transitions(
            transition_table, state,
            "\"" + key_name + "\":"
        )
    transition_table[(state, "n")] = f"NULL_N_{path}"
    transition_table[(f"NULL_N_{path}", "u")] = f"NULL_U_{path}"
    transition_table[(f"NULL_U_{path}", "l")] = f"NULL_L_{path}"
    transition_table[(f"NULL_L_{path}", "l")] = f"EXPECT_SEPARATOR_{path}"

    return f"EXPECT_SEPARATOR_{path}"


def _build_arg_object_transitions(
        transition_table: dict[tuple[str, str], str],
        arg_schema: dict, path: str, state: str,
        _: bool = True
) -> str:
    key_name = path.split(".")[-1]
    state = _build_key_transitions(
        transition_table, state,
        "\"" + key_name + "\":{"
    )
    properties = arg_schema["properties"]
    args_nb = len(properties)
    arg = ""
    for arg in properties:
        json_type = properties[arg].get("type")
        if json_type == "object":
            state = _build_arg_object_transitions(
                transition_table,
                properties[arg], f"{path}.{arg}",
                state
            )
        elif json_type == "array":
            state = _build_arg_array_transitions(
                transition_table,
                properties[arg], f"{path}.{arg}",
                state
            )
        elif json_type == "string":
            state = _build_arg_string_transitions(
                transition_table,
                properties[arg], f"{path}.{arg}",
                state
            )
        elif json_type == "integer":
            state = _build_arg_integer_transitions(
                transition_table,
                properties[arg], f"{path}.{arg}",
                state
            )
        elif json_type == "number":
            state = _build_arg_number_transitions(
                transition_table,
                properties[arg], f"{path}.{arg}",
                state
            )
        elif json_type == "boolean":
            state = _build_arg_boolean_transitions(
                transition_table,
                properties[arg], f"{path}.{arg}",
                state
            )
        elif json_type == "null":
            state = _build_arg_null_transitions(
                transition_table,
                properties[arg], f"{path}.{arg}",
                state
            )
        else:
            raise TypeError(
                f"`{json_type}` is not a valid JSON type. "
                "Supported types: string, integer, number,"
                " boolean, null, object, array"
            )
        args_nb -= 1
        separator = "}" if args_nb == 0 else ","
        transition_table[(state, separator)] = f"END_{path}.{arg}"
        state = f"END_{path}.{arg}"

    return f"END_{path}.{arg}"


def _build_arg_array_transitions(
        transition_table: dict[tuple[str, str], str],
        arg_schema: dict, path: str, state: str,
        _: bool = True
) -> str:
    key_name = path.split(".")[-1]
    state = _build_key_transitions(
        transition_table, state,
        "\"" + key_name + "\":["
    )
    json_type = arg_schema["items"].get("type")
    if json_type == "string":
        state = _build_arg_string_transitions(
            transition_table,
            arg_schema, path,
            state, False
        )
        transition_table[(state, ",")] = f"NEXT_STR_{path}"
        transition_table[(f"NEXT_STR_{path}", "\"")] = f"STR_{path}"
    elif json_type == "integer":
        state = _build_arg_integer_transitions(
            transition_table,
            arg_schema, path,
            state, False
        )
        transition_table[(state, ",")] = f"NEXT_NB_{path}"
        transition_table[(f"NEXT_NB_{path}", "-")] = f"WAIT_NB_{path}"
        transition_table[(f"NEXT_NB_{path}", "DIGIT")] = f"NB_{path}"
        transition_table[(f"WAIT_NB_{path}", "DIGIT")] = f"NB_{path}"
    elif json_type == "number":
        state = _build_arg_number_transitions(
            transition_table,
            arg_schema, path,
            state, False
        )
        transition_table[(state, ",")] = f"NEXT_NB_{path}"
        transition_table[(f"NEXT_NB_{path}", "-")] = f"WAIT_NB_{path}"
        transition_table[(f"NEXT_NB_{path}", "DIGIT")] = f"NB_{path}"
        transition_table[(f"WAIT_NB_{path}", "DIGIT")] = f"NB_{path}"
    elif json_type == "boolean":
        state = _build_arg_boolean_transitions(
            transition_table,
            arg_schema, path,
            state, False
        )
        transition_table[(state, ",")] = f"NEXT_BOOL_{path}"
        transition_table[(f"NEXT_BOOL_{path}", "t")] = f"BOOL_T_{path}"
        transition_table[(f"NEXT_BOOL_{path}", "f")] = f"BOOL_F_{path}"
    elif json_type == "null":
        state = _build_arg_null_transitions(
            transition_table,
            arg_schema, path,
            state, False
        )
        transition_table[(state, ",")] = f"NEXT_NULL_{path}"
        transition_table[(f"NEXT_NULL_{path}", "n")] = f"NULL_N_{path}"
    else:
        raise TypeError(
            f"`{json_type}` is not a valid JSON type. "
            "Supported types are: string, integer, number,"
            " boolean, null, object, array"
        )
    next_state = f"ARR_END_{path}"
    transition_table[(state, "]")] = next_state

    return next_state


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
        arg_schema: dict, path: str, state: str
) -> str:
    arg_type: str = arg_schema.get("type", "")
    builder: ArgBuilderType | None = ARG_TYPE_TO_BUILDER.get(arg_type, None)
    if not builder:
        raise TypeError(
            "This JSON type is not supported. "
            "Supported types are: string, integer, number,"
            " boolean, null, object, array"
        )
    return builder(
            transition_table,
            arg_schema, path,
            state, True
    )


def _build_func_params_transitions(
    transition_table: dict[tuple[str, str], str],
    func_params: dict, func_name: str, state: str
) -> None:
    len_fun_params = len(func_params)
    for arg in func_params:
        path = f"{func_name}.{arg}"
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
    func_definitions_path: str
) -> tuple[dict[tuple[str, str], str], set[str]]:
    with open(func_definitions_path, "r") as file:
        func_definitions_json = json.load(file)

    transition_table: dict[tuple[str, str], str] = {}
    func_name_states: set[str] = set()
    for func_definition in func_definitions_json:
        func = {
            "name": func_definition["name"],
            "parameters": func_definition["parameters"]
        }
        _build_func_transitions(transition_table, func_name_states, func)
    return transition_table, func_name_states


def build_outgoing_transitions(
    transition_table: dict[tuple[str, str], str]
) -> dict[str, list[tuple[str, str]]]:
    outgoing_transitions: dict[str, list[tuple[str, str]]] = {}

    for (state, input_category), next_state in transition_table.items():
        outgoing_transitions.setdefault(
            state, []
        ).append((input_category, next_state))

    return outgoing_transitions
