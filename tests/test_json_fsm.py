import pytest

from src.constrained_decoding.json_fsm import JSONSchemaFSM
from src.function_calling.func_definitions import FuncDefinitions, ParamModel


@pytest.fixture
def func_definitions() -> list[FuncDefinitions]:
    return [
        FuncDefinitions(
            name="fn_add_numbers",
            description="Add two numbers",
            parameters={
                "x1": ParamModel(type="number"),
                "x2": ParamModel(type="number")
            },
            returns=ParamModel(
                type="number"
            )
        ),
        FuncDefinitions(
            name="fn_mul_numbers",
            description="Multiply two numbers",
            parameters={
                "x1": ParamModel(type="number"),
                "x2": ParamModel(type="number")
            },
            returns=ParamModel(
                type="number"
            )
        ),
    ]


@pytest.fixture
def fsm(func_definitions: list[FuncDefinitions]) -> JSONSchemaFSM:
    return JSONSchemaFSM(func_definitions=func_definitions)


@pytest.fixture
def fsm_all_types() -> JSONSchemaFSM:
    """FSM with one function using every supported type."""
    return JSONSchemaFSM(func_definitions=[
        FuncDefinitions(
            name="fn_all",
            description="Every supported type",
            parameters={
                "s": ParamModel(type="string"),
                "i": ParamModel(type="integer"),
                "b": ParamModel(type="boolean"),
                "z": ParamModel(type="null"),
                "o": ParamModel(type="object", properties={
                    "a": ParamModel(type="integer"),
                    "c": ParamModel(type="object", properties={
                        "d": ParamModel(type="boolean")
                    })
                }),
                "ai": ParamModel(
                    type="array", items=ParamModel(type="integer")
                ),
                "ao": ParamModel(type="array", items=ParamModel(
                    type="object",
                    properties={"k": ParamModel(type="string")}
                )),
                "aa": ParamModel(type="array", items=ParamModel(
                    type="array", items=ParamModel(type="null")
                ))
            },
            returns=ParamModel(type="null")
        )
    ])


ADD_PARAMS = "fn_add_numbers\",\"parameters\":{"
MUL_PARAMS = "fn_mul_numbers\",\"parameters\":{"
PRINT_PARAMS = "fn_print_string\",\"parameters\":{"
ALL_PARAMS = 'fn_all","parameters":{'
ALL_I = 'END_fn_all.s"i":'
ALL_B = 'END_fn_all.i"b":'
ALL_Z = 'END_fn_all.b"z":'
ALL_O = 'END_fn_all.z"o":'
ALL_AI = 'END_fn_all.o"ai":'
ALL_AO = 'END_fn_all.ai"ao":'
ALL_AA = 'END_fn_all.ao"aa":'


def _feed(fsm: JSONSchemaFSM, text: str) -> str:
    """Feed every character of `text` and return the last state."""
    state = fsm.get_state()
    for char in text:
        state = fsm.transition(char)
    return state


def test_is_in_func_name(fsm: JSONSchemaFSM) -> None:
    assert fsm.is_in_func_name("") is True
    assert fsm.is_in_func_name("fn") is True
    assert fsm.is_in_func_name("_fn") is False
    assert fsm.is_in_func_name("invalid name") is False
    assert fsm.is_in_func_name("fn_add_numbers") is True
    assert fsm.is_in_func_name("fn_add_numbers\"") is False
    assert fsm.is_in_func_name("fn_add_numbers\",\"parameters\":{") is False
    assert fsm.is_in_func_name("fn_mul_numbers") is True
    assert fsm.is_in_func_name("fn_") is True
    assert fsm.is_in_func_name("fn_add_numbers_") is False
    assert fsm.is_in_func_name("FN") is False
    assert fsm.is_in_func_name("Fn_add_numbers") is False
    assert fsm.is_in_func_name("NB_fn_add_numbers.x1") is False
    assert fsm.is_in_func_name("END_fn_add_numbers}") is False
    assert fsm.is_in_func_name("ACCEPT") is False
    assert fsm.is_in_func_name("error") is False


def test_get_unique_outgoing_transition(fsm_all_types: JSONSchemaFSM) -> None:
    unique = fsm_all_types.get_unique_outgoing_transition
    assert unique("") == ("f", "f")
    assert unique("fn_a") == ("l", "fn_al")
    assert unique(ALL_I) is None
    assert unique("WAIT_NB_fn_all.i") == ("DIGIT", "NB_fn_all.i")
    assert unique("NB_fn_all.i") is None
    assert unique(ALL_B) is None
    assert unique("BOOL_T_fn_all.b") == ("r", "BOOL_R_fn_all.b")
    assert unique("BOOL_R_fn_all.b") == ("u", "BOOL_U_fn_all.b")
    assert unique("BOOL_U_fn_all.b") == ("e", "EXPECT_SEPARATOR_fn_all.b")
    assert unique("BOOL_F_fn_all.b") == ("a", "BOOL_A_fn_all.b")
    assert unique("BOOL_A_fn_all.b") == ("l", "BOOL_L_fn_all.b")
    assert unique("BOOL_L_fn_all.b") == ("s", "BOOL_S_fn_all.b")
    assert unique("BOOL_S_fn_all.b") == ("e", "EXPECT_SEPARATOR_fn_all.b")
    assert unique("EXPECT_SEPARATOR_fn_all.b") == (",", "END_fn_all.b")
    assert unique(ALL_Z) == ("n", "NULL_N_fn_all.z")
    assert unique("NULL_N_fn_all.z") == ("u", "NULL_U_fn_all.z")
    assert unique("NULL_U_fn_all.z") == ("l", "NULL_L_fn_all.z")
    assert unique("NULL_L_fn_all.z") == ("l", "EXPECT_SEPARATOR_fn_all.z")
    assert unique(ALL_O) == ("{", ALL_O + "{")
    assert unique(ALL_O + "{") == ("\"", ALL_O + "{\"")
    assert unique("END_fn_all.o.a") == ("\"", "END_fn_all.o.a\"")
    assert unique("EXPECT_SEPARATOR_fn_all.o.c.d") == (
        "}", "END_fn_all.o.c.d"
    )
    assert unique("END_fn_all.o.c.d") == ("}", "END_fn_all.o.c")
    assert unique("END_fn_all.o.c") == (",", "END_fn_all.o")
    assert unique(ALL_AI) == ("[", ALL_AI + "[")
    assert unique(ALL_AI + "[") is None
    assert unique("NEXT_fn_all.ai") is None
    assert unique("NB_fn_all.ai[]") is None
    assert unique("ARR_END_fn_all.ai") == (",", "END_fn_all.ai")
    assert unique(ALL_AO + "[") == ("{", ALL_AO + "[{")
    assert unique("NEXT_fn_all.ao") == ("{", "NEXT_fn_all.ao{")
    assert unique("NEXT_fn_all.ao{\"k\":") == ("\"", "STR_fn_all.ao[].k")
    assert unique("END_fn_all.ao[].k") is None
    assert unique(ALL_AA + "[") == ("[", ALL_AA + "[[")
    assert unique("NEXT_fn_all.aa") == ("[", "NEXT_fn_all.aa[")
    assert unique("NEXT_fn_all.aa[]") == ("n", "NULL_N_fn_all.aa[][]")
    assert unique("EXPECT_SEPARATOR_fn_all.aa[][]") is None
    assert unique("ARR_END_fn_all.aa[]") is None
    assert unique("ARR_END_fn_all.aa") == ("}", "END_fn_all}")
    assert unique("END_fn_all}") == ("}", "ACCEPT")


def test_transition(fsm_all_types: JSONSchemaFSM) -> None:
    fsm_all_types.set_state("")
    assert _feed(fsm_all_types, ALL_PARAMS + (
        '"s":"a\\n","i":-12,"b":true,"z":null,'
        '"o":{"a":-3,"c":{"d":true}},'
        '"ai":[-1,23,-4],'
        '"ao":[{"k":"x\\""},{"k":"y"}],'
        '"aa":[[null,null],[null]]}}'
    )) == "ACCEPT"
    fsm_all_types.set_state("")
    assert _feed(fsm_all_types, ALL_PARAMS + (
        '"s":"","i":7,"b":false,"z":null,'
        '"o":{"a":45,"c":{"d":false}},'
        '"ai":[5],'
        '"ao":[{"k":""}],'
        '"aa":[[null]]}}'
    )) == "ACCEPT"
    fsm_all_types.set_state(ALL_I)
    assert fsm_all_types.transition(".") == "error"
    assert fsm_all_types.transition("-") == "WAIT_NB_fn_all.i"
    assert fsm_all_types.transition(",") == "error"
    assert fsm_all_types.transition("-") == "error"
    assert fsm_all_types.transition("1") == "NB_fn_all.i"
    assert fsm_all_types.transition(".") == "error"
    assert fsm_all_types.transition("e") == "error"
    assert fsm_all_types.transition(",") == "END_fn_all.i"
    fsm_all_types.set_state(ALL_B)
    assert fsm_all_types.transition("T") == "error"
    assert fsm_all_types.transition("1") == "error"
    assert fsm_all_types.transition("\"") == "error"
    assert fsm_all_types.transition("n") == "error"
    assert _feed(fsm_all_types, "tru") == "BOOL_U_fn_all.b"
    assert fsm_all_types.transition(",") == "error"
    fsm_all_types.set_state(ALL_B)
    assert _feed(fsm_all_types, "fals") == "BOOL_S_fn_all.b"
    assert fsm_all_types.transition(",") == "error"
    assert fsm_all_types.transition("y") == "error"
    fsm_all_types.set_state(ALL_B)
    assert fsm_all_types.transition("f") == "BOOL_F_fn_all.b"
    assert fsm_all_types.transition("r") == "error"
    fsm_all_types.set_state(ALL_Z)
    assert fsm_all_types.transition("N") == "error"
    assert fsm_all_types.transition("t") == "error"
    assert _feed(fsm_all_types, "nul") == "NULL_L_fn_all.z"
    assert fsm_all_types.transition(",") == "error"
    fsm_all_types.set_state(ALL_O)
    assert fsm_all_types.transition("\"") == "error"
    assert fsm_all_types.transition("[") == "error"
    assert fsm_all_types.transition("{") == ALL_O + "{"
    assert fsm_all_types.transition("}") == "error"
    assert _feed(fsm_all_types, "\"") == ALL_O + "{\""
    assert fsm_all_types.transition("c") == "error"
    assert _feed(fsm_all_types, "a\":1") == "NB_fn_all.o.a"
    assert fsm_all_types.transition("}") == "error"
    assert _feed(fsm_all_types, ",\"c\":{\"d\":true") == \
        "EXPECT_SEPARATOR_fn_all.o.c.d"
    assert fsm_all_types.transition(",") == "error"
    assert fsm_all_types.transition("}") == "END_fn_all.o.c.d"
    assert fsm_all_types.transition(",") == "error"
    assert fsm_all_types.transition("}") == "END_fn_all.o.c"
    assert fsm_all_types.transition("}") == "error"
    fsm_all_types.set_state(ALL_AI)
    assert fsm_all_types.transition("1") == "error"
    assert fsm_all_types.transition("{") == "error"
    assert fsm_all_types.transition("[") == ALL_AI + "["
    assert fsm_all_types.transition("]") == "error"
    assert fsm_all_types.transition(",") == "error"
    assert fsm_all_types.transition("\"") == "error"
    assert fsm_all_types.transition("1") == "NB_fn_all.ai[]"
    assert fsm_all_types.transition(".") == "error"
    assert fsm_all_types.transition(",") == "NEXT_fn_all.ai"
    assert fsm_all_types.transition("]") == "error"
    assert fsm_all_types.transition(",") == "error"
    assert fsm_all_types.transition("2") == "NB_fn_all.ai[]"
    assert fsm_all_types.transition("]") == "ARR_END_fn_all.ai"
    assert fsm_all_types.transition("]") == "error"
    fsm_all_types.set_state(ALL_AO + "[")
    assert fsm_all_types.transition("\"") == "error"
    fsm_all_types.set_state("NEXT_fn_all.ao")
    assert fsm_all_types.transition("\"") == "error"
    assert fsm_all_types.transition("{") == "NEXT_fn_all.ao{"
    assert fsm_all_types.transition("}") == "error"
    fsm_all_types.set_state(ALL_AA + "[")
    assert fsm_all_types.transition("n") == "error"
    assert fsm_all_types.transition("]") == "error"
    fsm_all_types.set_state("NEXT_fn_all.aa")
    assert fsm_all_types.transition("n") == "error"
    fsm_all_types.set_state("EXPECT_SEPARATOR_fn_all.aa[][]")
    assert fsm_all_types.transition("}") == "error"
    fsm_all_types.set_state("ARR_END_fn_all.aa[]")
    assert fsm_all_types.transition("}") == "error"
    assert fsm_all_types.transition("]") == "ARR_END_fn_all.aa"
    assert fsm_all_types.transition(",") == "error"
    assert fsm_all_types.transition("]") == "error"


def test_get_input_category(
    fsm_all_types: JSONSchemaFSM
) -> None:
    fsm_all_types.set_state(ALL_I)
    assert fsm_all_types._get_input_category("0") == "DIGIT"
    assert fsm_all_types._get_input_category("-") == "-"
    fsm_all_types.set_state("NB_fn_all.i")
    assert fsm_all_types._get_input_category("9") == "DIGIT"
    assert fsm_all_types._get_input_category(".") == "."
    fsm_all_types.set_state(ALL_B)
    assert fsm_all_types._get_input_category("t") == "t"
    assert fsm_all_types._get_input_category("f") == "f"
    fsm_all_types.set_state(ALL_Z)
    assert fsm_all_types._get_input_category("n") == "n"
    fsm_all_types.set_state(ALL_O)
    assert fsm_all_types._get_input_category("{") == "{"
    fsm_all_types.set_state(ALL_AI)
    assert fsm_all_types._get_input_category("[") == "["
    fsm_all_types.set_state(ALL_AI + "[")
    assert fsm_all_types._get_input_category("3") == "DIGIT"
    fsm_all_types.set_state("NEXT_fn_all.ai")
    assert fsm_all_types._get_input_category("3") == "DIGIT"
    fsm_all_types.set_state("NB_fn_all.ai[]")
    assert fsm_all_types._get_input_category("]") == "]"
    fsm_all_types.set_state("STR_fn_all.ao[].k")
    assert fsm_all_types._get_input_category("a") == "CHAR"
    assert fsm_all_types._get_input_category("\"") == "\""
    fsm_all_types.set_state("ESC_fn_all.ao[].k")
    assert fsm_all_types._get_input_category("n") == "SPECIAL_CHAR"
    assert fsm_all_types._get_input_category("u") == "u"


@pytest.mark.parametrize("param, error_msg", [
    (ParamModel.model_construct(type="object"), "has no properties"),
    (ParamModel.model_construct(type="array"), "has no items"),
    (ParamModel.model_construct(type="tuple"), "Type `tuple` is not supported")
    ])
def test_empty_transitions(param: ParamModel, error_msg: str) -> None:
    func = FuncDefinitions.model_construct(
        name="fn", description="",
        parameters={"p": param}, returns=ParamModel(type="null")
    )
    with pytest.raises(ValueError, match=error_msg):
        JSONSchemaFSM(func_definitions=[func])
