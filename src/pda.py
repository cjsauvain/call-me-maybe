from dataclasses import dataclass, field


def pda_default_factory() -> dict:
    return {
        ("IN_STRING_VALUE", "ANY_CHARACTER"): "IN_STRING_VALUE",
        ("IN_STRING_VALUE", "\\"): "EXPECT_ESCAPED",
        ("IN_STRING_VALUE", "\""): "EXPECT_SEPARATOR",
        ("IN_DIGIT", "ANY_DIGIT"): "IN_DIGIT",
        ("IN_DIGIT", "."): "IN_DIGIT",
        ("IN_DIGIT", ","): "EXPECT_KEY",
        ("IN_STRING_KEY", "ANY_CHARACTER"): "IN_STRING_KEY",
        ("IN_STRING_KEY", "\""): "EXPECT_COLON",
        ("EXPECT_KEY", "\""): "IN_STRING_KEY",
        ("EXPECT_VALUE_OR_OBJECT", "{"): "EXPECT_KEY",
        ("EXPECT_VALUE_OR_OBJECT", "\""): "IN_STRING_VALUE",
        ("EXPECT_VALUE_OR_OBJECT", "ANY_DIGIT"): "IN_DIGIT",
        ("EXPECT_VALUE_OR_OBJECT", "-"): "IN_DIGIT",
        ("EXPECT_VALUE_OR_OBJECT", "ANY_LITERAL"): "EXPECT_SEPARATOR",
        ("EXPECT_SEPARATOR", ","): "EXPECT_KEY",
        ("EXPECT_SEPARATOR", "}"): "CLOSE_OBJECT",
        ("EXPECT_COLON", ":"): "EXPECT_VALUE_OR_OBJECT",
        ("EXPECT_ESCAPED", "IS_ANY_SPECIAL_CHARACTER"): "IN_STRING_VALUE",
    }


@dataclass
class PushDownAutomata:
    state: str = "IN_STRING_VALUE"
    stack: list = field(default_factory=list)
    transition_table: dict = field(default_factory=pda_default_factory)

    def transition(self, char: str) -> tuple[str, bool]:
        input_category = char
        to_append = char
        end = False

        if self.state in (
            "EXPECT_VALUE_OR_OBJECT", "IN_STRING_VALUE",
            "IN_STRING_KEY", "IN_DIGIT", "EXPECT_ESCAPED"
        ):
            literal = self.is_any_literal(char)
            if literal != "" and self.state == "EXPECT_VALUE_OR_OBJECT":
                to_append = literal
                input_category = "ANY_LITERAL"
            elif self.is_any_digit(char) and self.state in (
                "IN_DIGIT", "EXPECT_VALUE_OR_OBJECT"
            ):
                input_category = "ANY_DIGIT"
            elif self.is_any_special_character(char) and self.state == "EXPECT_ESCAPED":
                input_category = "ANY_SPECIAL_CHARACTER"
            elif self.is_any_character(char) and self.state in (
                "IN_STRING_KEY", "IN_STRING_VALUE"
            ):
                input_category = "ANY_CHARACTER"

        if char == "{" or char == "[":
            self.stack.append(char)
        elif char == "}" or char == "]":
            self.stack.pop()
            end = True if not self.stack else False
        
        print(f"char={char}, input_category={input_category}, state={self.state}", end=" ")
        self.state = self.transition_table.get((self.state, input_category))
        print(f"new_state={self.state}")
        if self.state is None:
            return "", True
        
        return to_append, end

    def is_any_character(self, char: str) -> bool:
        return (
            char not in ('"\\{}[]')
            and ord(char) >= 0x20
        )
    
    def is_any_literal(self, char: str) -> str:
        if char == "t":
            return "true"
        if char == "f":
            return "false"
        if char == "n":
            return "null"
        return ""
    
    def is_any_digit(self, char: str) -> bool:
        return char in "0123456789"

    def is_any_special_character(self, char: str) -> bool:
        return char in '"\\/bfnrt'
