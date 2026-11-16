from pydantic import BaseModel, ConfigDict


class FuncCallInput(BaseModel):
    """A prompt to turn into a function call.

    Attributes:
        prompt: Natural language request.
    """
    model_config = ConfigDict(extra='forbid')

    prompt: str
