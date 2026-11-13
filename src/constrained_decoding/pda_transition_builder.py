from collections import defaultdict
import json
import pprint


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
            state += char
    transition_table["FUNC_NAME"][(state, "\"")] = f"ACCEPT_{state}"


def _build_key_transitions(
        func_params_transition_table: dict,
        state: str, key: str
) -> str:
    for char in key:
        if func_params_transition_table.get((state, char)) is None:
            state = _add_new_entry(
                func_params_transition_table,
                state, char
            )
    return state


def _build_arg_string_transitions(
        func_params_transition_table: dict,
        _: dict, arg_name: str, state: str,
        add_key: bool = True
) -> str:
    if add_key:
        state = _build_key_transitions(
            func_params_transition_table, state,
            "\"" + arg_name + "\":"
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

    return f"EXPECT_SEPARATOR_{arg_name}"


def _build_arg_number_transitions(
        func_params_transition_table: dict,
        _: dict, arg_name: str, state: str,
        add_key: bool = True
) -> str:
    if add_key:
        state = _build_key_transitions(
            func_params_transition_table, state,
            "\"" + arg_name + "\":"
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

    return f"NB_{arg_name}"


def _build_arg_boolean_transitions(
        func_params_transition_table: dict,
        _: dict, arg_name: str, state: str,
        add_key: bool = True
) -> str:
    if add_key:
        state = _build_key_transitions(
            func_params_transition_table, state,
            "\"" + arg_name + "\":"
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

    return f"EXPECT_SEPARATOR_{arg_name}"


def _build_arg_null_transitions(
        func_params_transition_table: dict,
        _: dict, arg_name: str, state: str,
        add_key: bool = True
) -> str:
    if add_key:
        state = _build_key_transitions(
            func_params_transition_table, state,
            "\"" + arg_name + "\":"
        )
    func_params_transition_table[(state, "n")] = \
        f"NULL_N_{arg_name}"
    func_params_transition_table[(f"NULL_N_{arg_name}", "u")] = \
        f"NULL_U_{arg_name}"
    func_params_transition_table[(f"NULL_U_{arg_name}", "l")] = \
        f"NULL_L_{arg_name}"
    func_params_transition_table[(f"NULL_L_{arg_name}", "l")] = \
        f"EXPECT_SEPARATOR_{arg_name}"

    return f"EXPECT_SEPARATOR_{arg_name}"


def _build_arg_object_transitions(
        func_params_transition_table: dict,
        arg_schema: dict, arg_name: str,
        state: str
) -> str:
    state = _build_key_transitions(
        func_params_transition_table, state,
        "\"" + arg_name + "\":{"
    )
    args_nb = len(arg_schema)
    properties = arg_schema["properties"]
    for arg in properties:
        json_type = properties[arg].get("type")
        if json_type == "object":
            state = _build_arg_object_transitions(
                func_params_transition_table,
                properties[arg], arg,
                state
            )
        elif json_type == "array":
            state = _build_arg_array_transitions(
                func_params_transition_table,
                properties[arg], arg,
                state
            )
        elif json_type == "string":
            state = _build_arg_string_transitions(
                func_params_transition_table,
                properties[arg], arg,
                state
            )
        elif json_type == "number":
            state = _build_arg_number_transitions(
                func_params_transition_table,
                properties[arg], arg,
                state
            )
            func_params_transition_table[(f"NB_DECIMAL_{arg}", "]")] = \
                f"END_{arg_name}"
        elif json_type == "boolean":
            state = _build_arg_boolean_transitions(
                func_params_transition_table,
                properties[arg], arg,
                state
            )
        elif json_type == "null":
            state = _build_arg_null_transitions(
                func_params_transition_table,
                properties[arg], arg,
                state
            )
        else:
            print(arg_schema)
            raise TypeError(
                f"`{type}` is not a valid JSON type. "
                "Supported types: string, number, boolean, null, object, array"
            )
        args_nb -= 1
        separator = "}" if args_nb == 0 else ","
        func_params_transition_table[(state, separator)] = f"END_{arg}"
        state = f"END_{arg}"

    return state


def _build_arg_array_transitions(
        func_params_transition_table: dict,
        arg_schema: dict, arg_name: str,
        state: str
) -> str:
    state = _build_key_transitions(
        func_params_transition_table, state,
        "\"" + arg_name + "\":["
    )
    json_type = arg_schema["items"].get("type")
    if json_type == "string":
        state = _build_arg_string_transitions(
            func_params_transition_table,
            arg_schema, arg_name,
            state, False
        )
        func_params_transition_table[(state, ",")] = f"NEXT_STR_{arg_name}"
        func_params_transition_table[(f"NEXT_STR_{arg_name}", "\"")] = \
            f"STR_{arg_name}"
    elif json_type == "number":
        state = _build_arg_number_transitions(
            func_params_transition_table,
            arg_schema, arg_name,
            state, False
        )
        func_params_transition_table[(state, ",")] = f"NEXT_NB_{arg_name}"
        func_params_transition_table[(f"NEXT_NB_{arg_name}", "-")] = \
            f"NB_{arg_name}"
        func_params_transition_table[(f"NEXT_NB_{arg_name}", "DIGIT")] = \
            f"NB_{arg_name}"
        func_params_transition_table[(f"NB_DECIMAL_{arg_name}", "]")] = \
            f"END_{arg_name}"
    elif json_type == "boolean":
        state = _build_arg_boolean_transitions(
            func_params_transition_table,
            arg_schema, arg_name,
            state, False
        )
        func_params_transition_table[(state, ",")] = f"NEXT_BOOL_{arg_name}"
        func_params_transition_table[(f"NEXT_BOOL_{arg_name}", "t")] = \
            f"BOOL_T_{arg_name}"
        func_params_transition_table[(f"NEXT_BOOL_{arg_name}", "f")] = \
            f"BOOL_F_{arg_name}"
    elif json_type == "null":
        state = _build_arg_null_transitions(
            func_params_transition_table,
            arg_schema, arg_name,
            state, False
        )
        func_params_transition_table[(state, ",")] = f"NEXT_NULL_{arg_name}"
        func_params_transition_table[(f"NEXT_NULL_{arg_name}", "n")] = \
            f"BOOL_N_{arg_name}"
    else:
        raise TypeError(
            f"`{type}` is not a valid JSON type. "
            "Supported types are: string, number, boolean, null, object, array"
        )
    func_params_transition_table[(state, "]")] = f"EXPECT_SEPARATOR_{arg_name}"
    func_params_transition_table[(f"EXPET_SEPARATOR_{arg_name}", ",")] = \
        f"END_{arg_name}"


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
) -> str:
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
    func_params: str, func_name: str
):
    transition_table[func_name] = {}
    state = ""
    len_fun_params = len(func_params)
    for arg in func_params:
        state = _build_arg_transitions(
            transition_table[func_name],
            func_params[arg], arg, state
        )
        len_fun_params -= 1
        if len_fun_params > 0:
            transition_table[func_name][(state, ",")] = f"END_{arg}"
            if state == f"NB_{arg}":
                transition_table[func_name][(f"NB_DECIMAL_{arg}", ",")] = \
                    f"END_{arg}"
            state = f"END_{arg}"
    transition_table[func_name][(state, "}")] = "ACCEPT"
    if state == f"NB_{arg}":
        transition_table[func_name][(f"NB_DECIMAL_{arg}", "}")] = "ACCEPT"


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

    with open("transition_table.json", "w") as file:
        pprint.pprint(transition_table, stream=file, indent=4)
    return transition_table
