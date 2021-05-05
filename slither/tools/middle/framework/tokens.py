from abc import ABC, abstractmethod
from collections import Callable

from slither.slithir.operations import InternalCall, HighLevelCall, SolidityCall


class Token(ABC):
    def __init__(self, assoc_stmt, func):
        self.bindings: dict = {}
        self.assoc_stmt = assoc_stmt
        self.func = func
        self.annotation = None

    def single_click(self):
        if self.bindings["single-click"] is not None:
            self.bindings["single-click"]()

    def double_click(self):
        if self.bindings["double-click"] is not None:
            self.bindings["double-click"]()

    def right_click(self):
        if self.bindings["right-click"] is not None:
            self.bindings["right-click"]()

    def set_binding_single_click(self, callback: Callable):
        self.bindings["single-click"] = callback

    def set_binding_double_click(self, callback: Callable):
        self.bindings["double-click"] = callback

    def set_binding_right_click(self, callback: Callable):
        self.bindings["right-click"] = callback

    def render_annotation(self):
        return "" if self.annotation is None else self.annotation.render()

    def render_with_annotation(self):
        regular = self.render()
        extension = self.render_annotation()
        if extension != "":
            return regular + ": " + extension
        return regular

    @abstractmethod
    def render(self):
        pass


class Keyword(Token):
    def __init__(self, literal: str, assoc_stmt, func):
        super().__init__(assoc_stmt, func)
        self.literal: str = literal

    def render(self):
        return self.literal


class LeftParen(Token):
    def __init__(self, assoc_stmt, func):
        super().__init__(assoc_stmt, func)

    def render(self):
        return "("


class RightParen(Token):
    def __init__(self, assoc_stmt, func):
        super().__init__(assoc_stmt, func)

    def render(self):
        return ")"


class LeftBrace(Token):
    def __init__(self, assoc_stmt, func):
        super().__init__(assoc_stmt, func)

    def render(self):
        return "{"


class RightBrace(Token):
    def __init__(self, assoc_stmt, func):
        super().__init__(assoc_stmt, func)

    def render(self):
        return "}"


class Not(Token):
    def __init__(self, assoc_stmt, func):
        super().__init__(assoc_stmt, func)

    def render(self):
        return "!"


class Variable(Token):
    def __init__(self, var, assoc_stmt, func):
        super().__init__(assoc_stmt, func)
        assert var is not None
        self.var = var

    def render(self):
        return str(self.var)


class Literal(Token):
    def __init__(self, literal, assoc_stmt, func):
        super().__init__(assoc_stmt, func)
        self.literal = literal

    def render(self):
        return str(self.literal)


class NewLine(Token):
    def __init__(self, assoc_stmt, func):
        super().__init__(assoc_stmt, func)

    def render(self):
        return str("\n")


class Equals(Token):
    def __init__(self, assoc_stmt, func):
        super().__init__(assoc_stmt, func)

    def render(self):
        return str("=")


class Indent(Token):
    def __init__(self, assoc_stmt, func):
        super().__init__(assoc_stmt, func)

    def render(self):
        return str("")


class Value(Token):
    def __init__(self, value, variable, assoc_stmt, func):
        super().__init__(assoc_stmt, func)
        self.value = value
        self.variable = variable

    def render(self):
        return str(self.value)


class CallSite(Token):
    def __init__(self, assoc_stmt, func):
        super().__init__(assoc_stmt, func)

    def render(self):
        if isinstance(self.assoc_stmt, InternalCall):
            return self.assoc_stmt.function_name
        if isinstance(self.assoc_stmt, HighLevelCall):
            return self.assoc_stmt.function_name
        if isinstance(self.assoc_stmt, SolidityCall):
            return str(self.assoc_stmt.function)
        return "LOOP " + self.assoc_stmt.dest.name.lower()

    def __eq__(self, other):
        if not isinstance(other, CallSite):
            return False
        # Use referential equality for constituents.
        return (
            isinstance(self, CallSite)
            and isinstance(self, CallSite)
            and self.assoc_stmt == other.assoc_stmt
            and self.func == other.func
        )


class Annotation:
    def __init__(self, value):
        self.value = value

    def render(self):
        return str(self.value)
