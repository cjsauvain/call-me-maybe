import pytest
from pytest_mock import MockerFixture

from src.constrained_decoding.constrained_decoder import ConstrainedDecoder
from src.constrained_decoding.json_fsm import JSONSchemaFSM
from src.function_calling.func_definitions import FuncDefinitions, ParamModel


@pytest.fixture
def func_definitions() -> list[FuncDefinitions]:
    return [
        FuncDefinitions(
            name="fn_test",
            description="",
            parameters={"key": ParamModel(type="boolean")},
            returns=ParamModel(type="null")
        ),
        FuncDefinitions(
            name="fn_test2",
            description="",
            parameters={"name": ParamModel(type="string")},
            returns=ParamModel(type="null")
        )
    ]


@pytest.fixture
def fsm(func_definitions: list[FuncDefinitions]) -> JSONSchemaFSM:
    return JSONSchemaFSM(func_definitions=func_definitions)


@pytest.fixture
def constrained_decoder(
        mocker: MockerFixture, fsm: JSONSchemaFSM
) -> ConstrainedDecoder:
    return ConstrainedDecoder.model_construct(
        model=mocker.MagicMock(),
        fsm=fsm
    )


def test_decode(
        mocker: MockerFixture,
        constrained_decoder: ConstrainedDecoder
) -> None:
    logits: list[float] = [0.1, 0.5, 0.7]
    constrained_decoder.vocab = ["5", "r", "a"]
    constrained_decoder.fsm.set_state("BOOL_T_fn_test.key")
    assert constrained_decoder.decode(logits) == (1, "BOOL_R_fn_test.key")
    constrained_decoder.vocab = ["5", "ru", "a"]
    assert constrained_decoder.decode(logits) == (1, "BOOL_U_fn_test.key")
    constrained_decoder.vocab = ["5", "rux", "a"]
    assert constrained_decoder.decode(logits) is None
    constrained_decoder.fsm.set_state("BOOL_R_fn_test.key")

    assert constrained_decoder.decode(logits) is None

    logits = [0.1, 0.5, 0.7]
    constrained_decoder.vocab = ["5", "r", ""]
    assert constrained_decoder.decode(logits) is None

    mocker.patch("src.constrained_decoding.constrained_decoder.VOCAB_SIZE", 3)
    logits = [0.1, 0.5, 0.7, 0.9]
    constrained_decoder.vocab = ["u", "u", "u"]
    assert constrained_decoder.decode(logits) == (2, "BOOL_U_fn_test.key")

    assert constrained_decoder.fsm.get_state() == "BOOL_R_fn_test.key"
    constrained_decoder.fsm.set_state("BOOL_U_fn_test.key")

    logits = [0.1, 0.5, 0.7]
    constrained_decoder.vocab = ["5", "r", "n"]
    assert constrained_decoder.decode(logits) is None

    logits = []
    constrained_decoder.vocab = ["5", "r", ""]
    assert constrained_decoder.decode(logits) is None


def test_retrieve_forced_text(constrained_decoder: ConstrainedDecoder) -> None:
    constrained_decoder.fsm.set_state("fn_test\"")
    assert constrained_decoder.retrieve_forced_text() == \
        ",\"parameters\":{\"key\":"
    assert constrained_decoder.fsm.get_state() == \
        "fn_test\",\"parameters\":{\"key\":"

    constrained_decoder.fsm.set_state("fn_test2\",\"parameters\":{\"na")
    assert constrained_decoder.retrieve_forced_text() == "me\":\""

    constrained_decoder.fsm.set_state("END_fn_test2}")
    assert constrained_decoder.retrieve_forced_text() == ""
