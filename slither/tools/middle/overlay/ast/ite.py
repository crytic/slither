from slither.tools.middle.framework.tokens import Variable, Equals, Keyword, NewLine, Indent
from slither.tools.middle.overlay.ast.node import OverlayNode
from slither.core.cfg.node import NodeType


class OverlayITE(OverlayNode):
    """
    If Then Else (ITE) Node

    This node is used for conditional assignment between two possibilities. Used
    as an Overlay analog to Phi nodes.
    """

    def __init__(self, lvalue, condition, consequence, alternative):
        super().__init__(NodeType.OVERLAY)
        self.lvalue = lvalue
        self.condition = condition
        self.consequence = consequence
        self.alternative = alternative

    def __str__(self):
        return "OVERLAY ITE\n{} = if {} then {} else {}".format(
            self.lvalue, self.condition, self.consequence, self.alternative
        )

    def to_tokens(self, func, indent=0):
        token_list = [Indent(self, func) for _ in range(indent)]
        token_list.extend(
            [
                Variable(self.lvalue, self, func),
                Equals(self, func),
                Keyword("if", self, func),
                Variable(self.condition, self, func),
                Keyword("then", self, func),
                Variable(self.consequence, self, func),
                Keyword("else", self, func),
                Variable(self.alternative, self, func),
                NewLine(self, func),
            ]
        )
        return token_list
