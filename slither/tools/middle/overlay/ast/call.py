from collections import defaultdict
from typing import List

from slither.core.cfg.node import NodeType
from slither.tools.middle.framework.tokens import (
    Keyword,
    LeftParen,
    Variable,
    Not,
    LeftBrace,
    RightBrace,
    NewLine,
    RightParen,
    Literal,
    Indent,
    Token,
)
from slither.tools.middle.overlay.ast.node import OverlayNode


class OverlayCall(OverlayNode):
    ir: list

    def __init__(self, dest, cond=None):
        self.dest = dest
        self.ir = []
        self.cond = cond
        self.cond_complement = False
        self.loop_call = False
        self.loop_continue = False
        self.arg_as_map = defaultdict(list)
        self.ret_as_map = defaultdict(list)

        self.arguments = set()
        self.returns = set()
        super().__init__(NodeType.OVERLAY)

    def __str__(self):
        return "{}{}CALL {} if{} {}\n    Arguments {}\n    Returns {}".format(
            "LOOP " if self.loop_call else "",
            "CONT " if self.loop_continue else "",
            self.dest.name,
            " NOT" if self.cond_complement else "",
            self.cond if self.cond is not None else "TRUE",
            self.get_argument_str(),
            self.get_return_str(),
        )

    def get_argument_str(self) -> str:
        fragments = []
        for imported in self.arguments:
            if str(imported) in self.arg_as_map:
                fragments.append(
                    "{} as {}".format(
                        str([str(x) for x in self.arg_as_map[str(imported)]]), str(imported)
                    )
                )
            else:
                fragments.append(str(imported))
        return ",".join(fragments)

    def get_return_str(self) -> str:
        fragments = []
        for exported in self.returns:
            if str(exported) in self.ret_as_map:
                fragments.append(
                    "{} as {}".format(
                        str([str(x) for x in self.ret_as_map[str(exported)]]), str(exported)
                    )
                )
            else:
                fragments.append(str(exported))
        return ",".join(fragments)

    def to_tokens(self, func, body: List[Token] = None, indent=0):
        def append_with_indent(l, element):
            l.extend([(Indent(self, func)) for _ in range(indent)])
            l.append(element)

        def append(l, element):
            l.append(element)

        token_list = []
        append_with_indent(token_list, Keyword("if", self, func))
        append(token_list, LeftParen(self, func))
        if self.cond_complement:
            append(token_list, Not(self, func))
        append(token_list, Variable(self.cond, self, func))
        append(token_list, RightParen(self, func))
        append(token_list, LeftBrace(self, func))
        append(token_list, NewLine(self, func))

        if body is None:
            append_with_indent(token_list, Indent(self, func))
            append(token_list, Literal(self.dest.name, self, func))
            append(token_list, NewLine(self, func))
        else:
            if not any(isinstance(x, Variable) for x in body):
                # There is nothing explorable in body.
                return []

            prev = NewLine(self, func)
            for line in body:
                # Only add an indent if the previous character was a newline
                if isinstance(prev, NewLine):
                    append_with_indent(token_list, Indent(self, func))
                token_list.append(line)
                prev = line

        append_with_indent(token_list, RightBrace(self, func))
        append(token_list, NewLine(self, func))
        return token_list

    def __copy__(self):
        return OverlayCall(self.dest, self.cond)
