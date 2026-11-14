import json


def _add_new_entry(any_transition_table: dict, state: str, char: str) -> str:
    new_state = f"{state}{char}"
    any_transition_table[(state, char)] = new_state
    return new_state


def _build_func_name_transitions(transition_table: dict, func_name: str):
    state = ""
    for char in func_name:
        if not transition_table["FUNC_NAME"].get((state, char)):
            state = _add_new_entry(
                transition_table["FUNC_NAME"],
                state, char
            )
        else:
            state = transition_table["FUNC_NAME"][(state, char)]
    transition_table["FUNC_NAME"][(state, "\"")] = f"ACCEPT_{state}"


def _build_key_transitions(
        func_params_transition_table: dict,
        state: str, key: str
) -> str:
    for char in key:
        if not func_params_transition_table.get((state, char)):
            state = _add_new_entry(
                func_params_transition_table,
                state, char
            )
        else:
            state = func_params_transition_table[(state, char)]
    return state


def _build_arg_string_transitions(
        func_params_transition_table: dict,
        _: dict, arg_name: str, state: str,
        add_key: bool = True
) -> list[str]:
    if add_key:
        key_name = arg_name.split(".")[-1]
        state = _build_key_transitions(
            func_params_transition_table, state,
            "\"" + key_name + "\":"
        )
    func_params_transition_table[(state, "\"")] = f"STR_{arg_name}"
    func_params_transition_table[(f"STR_{arg_name}", "\\")] = \
        f"ESC_{arg_name}"
    func_params_transition_table[(f"STR_{arg_name}", "CHAR")] = \
        f"STR_{arg_name}"
    func_params_transition_table[(f"ESC_{arg_name}", "SPECIAL_CHAR")] = \
        f"STR_{arg_name}"
    func_params_transition_table[(f"STR_{arg_name}", "\"")] = \
        f"EXPECT_SEPARATOR_{arg_name}"

    return [f"EXPECT_SEPARATOR_{arg_name}"]


def _build_arg_number_transitions(
        func_params_transition_table: dict,
        _: dict, arg_name: str, state: str,
        add_key: bool = True
) -> list[str]:
    if add_key:
        key_name = arg_name.split(".")[-1]
        state = _build_key_transitions(
            func_params_transition_table, state,
            "\"" + key_name + "\":"
        )
    func_params_transition_table[(state, "-")] = \
        f"NB_{arg_name}"
    func_params_transition_table[(state, "DIGIT")] = \
        f"NB_{arg_name}"
    func_params_transition_table[(f"NB_{arg_name}", "DIGIT")] = \
        f"NB_{arg_name}"
    func_params_transition_table[(f"NB_{arg_name}", ".")] = \
        f"NB_DECIMAL_{arg_name}"
    func_params_transition_table[(f"NB_DECIMAL_{arg_name}", "DIGIT")] = \
        f"NB_DECIMAL_{arg_name}"

    return [f"NB_{arg_name}", f"NB_DECIMAL_{arg_name}"]


def _build_arg_boolean_transitions(
        func_params_transition_table: dict,
        _: dict, arg_name: str, state: str,
        add_key: bool = True
) -> list[str]:
    if add_key:
        key_name = arg_name.split(".")[-1]
        state = _build_key_transitions(
            func_params_transition_table, state,
            "\"" + key_name + "\":"
        )
    func_params_transition_table[(state, "t")] = \
        f"BOOL_T_{arg_name}"
    func_params_transition_table[(f"BOOL_T_{arg_name}", "r")] = \
        f"BOOL_R_{arg_name}"
    func_params_transition_table[(f"BOOL_R_{arg_name}", "u")] = \
        f"BOOL_U_{arg_name}"
    func_params_transition_table[(f"BOOL_U_{arg_name}", "e")] = \
        f"EXPECT_SEPARATOR_{arg_name}"
    func_params_transition_table[(state, "f")] = \
        f"BOOL_F_{arg_name}"
    func_params_transition_table[(f"BOOL_F_{arg_name}", "a")] = \
        f"BOOL_A_{arg_name}"
    func_params_transition_table[(f"BOOL_A_{arg_name}", "l")] = \
        f"BOOL_L_{arg_name}"
    func_params_transition_table[(f"BOOL_L_{arg_name}", "s")] = \
        f"BOOL_S_{arg_name}"
    func_params_transition_table[(f"BOOL_S_{arg_name}", "e")] = \
        f"EXPECT_SEPARATOR_{arg_name}"

    return [f"EXPECT_SEPARATOR_{arg_name}"]


def _build_arg_null_transitions(
        func_params_transition_table: dict,
        _: dict, arg_name: str, state: str,
        add_key: bool = True
) -> list[str]:
    if add_key:
        key_name = arg_name.split(".")[-1]
        state = _build_key_transitions(
            func_params_transition_table, state,
            "\"" + key_name + "\":"
        )
    func_params_transition_table[(state, "n")] = \
        f"NULL_N_{arg_name}"
    func_params_transition_table[(f"NULL_N_{arg_name}", "u")] = \
        f"NULL_U_{arg_name}"
    func_params_transition_table[(f"NULL_U_{arg_name}", "l")] = \
        f"NULL_L_{arg_name}"
    func_params_transition_table[(f"NULL_L_{arg_name}", "l")] = \
        f"EXPECT_SEPARATOR_{arg_name}"

    return [f"EXPECT_SEPARATOR_{arg_name}"]


def _build_arg_object_transitions(
        func_params_transition_table: dict,
        arg_schema: dict, arg_name: str,
        state: str
) -> list[str]:
    key_name = arg_name.split(".")[-1]
    state = _build_key_transitions(
        func_params_transition_table, state,
        "\"" + key_name + "\":{"
    )
    states = []
    properties = arg_schema["properties"]
    args_nb = len(properties)
    for arg in properties:
        json_type = properties[arg].get("type")
        if json_type == "object":
            states = _build_arg_object_transitions(
                func_params_transition_table,
                properties[arg], f"{arg_name}.{arg}",
                state
            )
        elif json_type == "array":
            states = _build_arg_array_transitions(
                func_params_transition_table,
                properties[arg], f"{arg_name}.{arg}",
                state
            )
        elif json_type == "string":
            states = _build_arg_string_transitions(
                func_params_transition_table,
                properties[arg], f"{arg_name}.{arg}",
                state
            )
        elif json_type == "number":
            states = _build_arg_number_transitions(
                func_params_transition_table,
                properties[arg], f"{arg_name}.{arg}",
                state
            )
        elif json_type == "boolean":
            states = _build_arg_boolean_transitions(
                func_params_transition_table,
                properties[arg], f"{arg_name}.{arg}",
                state
            )
        elif json_type == "null":
            states = _build_arg_null_transitions(
                func_params_transition_table,
                properties[arg], f"{arg_name}.{arg}",
                state
            )
        else:
            raise TypeError(
                f"`{type}` is not a valid JSON type. "
                "Supported types: string, number, boolean, null, object, array"
            )
        args_nb -= 1
        separator = "}" if args_nb == 0 else ","
        for s in states:
            func_params_transition_table[(s, separator)] = \
                f"END_{arg_name}.{arg}"
        state = f"END_{arg_name}.{arg}"

    return [f"END_{arg_name}.{arg}"]


def _build_arg_array_transitions(
        func_params_transition_table: dict,
        arg_schema: dict, arg_name: str,
        state: str
) -> list[str]:
    key_name = arg_name.split(".")[-1]
    state = _build_key_transitions(
        func_params_transition_table, state,
        "\"" + key_name + "\":["
    )
    states = []
    json_type = arg_schema["items"].get("type")
    if json_type == "string":
        states = _build_arg_string_transitions(
            func_params_transition_table,
            arg_schema, arg_name,
            state, False
        )
        func_params_transition_table[(states[0], ",")] = f"NEXT_STR_{arg_name}"
        func_params_transition_table[(f"NEXT_STR_{arg_name}", "\"")] = \
            f"STR_{arg_name}"
    elif json_type == "number":
        states = _build_arg_number_transitions(
            func_params_transition_table,
            arg_schema, arg_name,
            state, False
        )
        func_params_transition_table[(states[0], ",")] = f"NEXT_NB_{arg_name}"
        func_params_transition_table[(states[1], ",")] = f"NEXT_NB_{arg_name}"
        func_params_transition_table[(f"NEXT_NB_{arg_name}", "-")] = \
            f"NB_{arg_name}"
        func_params_transition_table[(f"NEXT_NB_{arg_name}", "DIGIT")] = \
            f"NB_{arg_name}"
    elif json_type == "boolean":
        states = _build_arg_boolean_transitions(
            func_params_transition_table,
            arg_schema, arg_name,
            state, False
        )
        func_params_transition_table[(states[0], ",")] = \
            f"NEXT_BOOL_{arg_name}"
        func_params_transition_table[(f"NEXT_BOOL_{arg_name}", "t")] = \
            f"BOOL_T_{arg_name}"
        func_params_transition_table[(f"NEXT_BOOL_{arg_name}", "f")] = \
            f"BOOL_F_{arg_name}"
    elif json_type == "null":
        states = _build_arg_null_transitions(
            func_params_transition_table,
            arg_schema, arg_name,
            state, False
        )
        func_params_transition_table[(states[0], ",")] = \
            f"NEXT_NULL_{arg_name}"
        func_params_transition_table[(f"NEXT_NULL_{arg_name}", "n")] = \
            f"NULL_N_{arg_name}"
    else:
        raise TypeError(
            f"`{type}` is not a valid JSON type. "
            "Supported types are: string, number, boolean, null, object, array"
        )
    end_state = f"ARR_END_{arg_name}"
    for s in states:
        func_params_transition_table[(s, "]")] = end_state

    return [end_state]


ARG_TYPE_TO_BUILDER = {
    "string": _build_arg_string_transitions,
    "number": _build_arg_number_transitions,
    "boolean": _build_arg_boolean_transitions,
    "null": _build_arg_null_transitions,
    "object": _build_arg_object_transitions,
    "array": _build_arg_array_transitions
}


def _build_arg_transitions(
        func_params_transition_table: dict,
        arg_schema: dict, arg_name: str,
        state: str
) -> list[str]:
    type = arg_schema.get("type", "")
    builder = ARG_TYPE_TO_BUILDER.get(type, None)
    if not builder:
        raise TypeError(
            "This JSON type is not supported."
            "Supported types are: string, number, boolean, null, object, array"
        )
    return builder(
            func_params_transition_table,
            arg_schema, arg_name,
            state
    )


def _build_func_params_transitions(
    transition_table: dict,
    func_params: dict, func_name: str
):
    transition_table[func_name] = {}
    state = ""
    states = []
    len_fun_params = len(func_params)
    for arg in func_params:
        states = _build_arg_transitions(
            transition_table[func_name],
            func_params[arg], arg, state
        )
        len_fun_params -= 1
        if len_fun_params > 0:
            for s in states:
                transition_table[func_name][(s, ",")] = f"END_{arg}"
            state = f"END_{arg}"
    for s in states:
        transition_table[func_name][(s, "}")] = "ACCEPT"


def _build_func_transitions(transition_table: dict, func: dict):
    _build_func_name_transitions(transition_table, func["name"])
    _build_func_params_transitions(
        transition_table,
        func["parameters"],
        func["name"]
    )


def build_transition_table(func_definitions_path: str) -> dict[str, dict]:
    with open(func_definitions_path, "r") as file:
        func_definitions_json = json.load(file)

    transition_table: dict[str, dict] = {
        "FUNC_NAME": {},
    }
    for func_definition in func_definitions_json:
        func = {
            "name": func_definition["name"],
            "parameters": func_definition["parameters"]
        }
        _build_func_transitions(transition_table, func)
    return transition_table
