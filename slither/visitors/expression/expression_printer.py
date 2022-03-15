from slither.visitors.expression.expression import ExpressionVisitor


def get(expression):
    val = expression.context["ExpressionPrinter"]
    # we delete the item to reduce memory use
    del expression.context["ExpressionPrinter"]
    return val


def set_val(expression, val):
    expression.context["ExpressionPrinter"] = val


class ExpressionPrinter(ExpressionVisitor):
    def result(self):
        if not self._result:
            self._result = get(self.expression)
        return self._result

    def _post_assignement_operation(self, expression):
        left = get(expression.expression_left)
        right = get(expression.expression_right)
        val = f"{left} {expression.type} {right}"
        set_val(expression, val)

    def _post_binary_operation(self, expression):
        left = get(expression.expression_left)
        right = get(expression.expression_right)
        val = f"{left} {expression.type} {right}"
        set_val(expression, val)

    def _post_call_expression(self, expression):
        called = get(expression.called)
        arguments = ",".join([get(x) for x in expression.arguments if x])
        val = f"{called}({arguments})"
        set_val(expression, val)

    def _post_conditional_expression(self, expression):
        if_expr = get(expression.if_expression)
        else_expr = get(expression.else_expression)
        then_expr = get(expression.then_expression)
        val = f"if {if_expr} then {else_expr} else {then_expr}"
        set_val(expression, val)

    def _post_elementary_type_name_expression(self, expression):
        set_val(expression, str(expression.type))

    def _post_identifier(self, expression):
        set_val(expression, str(expression.value))

    def _post_index_access(self, expression):
        left = get(expression.expression_left)
        right = get(expression.expression_right)
        val = f"{left}[{right}]"
        set_val(expression, val)

    def _post_literal(self, expression):
        set_val(expression, str(expression.value))

    def _post_member_access(self, expression):
        expr = get(expression.expression)
        member_name = str(expression.member_name)
        val = f"{expr}.{member_name}"
        set_val(expression, val)

    def _post_new_array(self, expression):
        array = str(expression.array_type)
        depth = expression.depth
        val = f"new {array}{'[]' * depth}"
        set_val(expression, val)

    def _post_new_contract(self, expression):
        contract = str(expression.contract_name)
        val = f"new {contract}"
        set_val(expression, val)

    def _post_new_elementary_type(self, expression):
        t = str(expression.type)
        val = f"new {t}"
        set_val(expression, val)

    def _post_tuple_expression(self, expression):
        expressions = [get(e) for e in expression.expressions if e]
        val = f"({','.join(expressions)})"
        set_val(expression, val)

    def _post_type_conversion(self, expression):
        t = str(expression.type)
        expr = get(expression.expression)
        val = f"{t}({expr})"
        set_val(expression, val)

    def _post_unary_operation(self, expression):
        t = str(expression.type)
        expr = get(expression.expression)
        if expression.is_prefix:
            val = f"{t}{expr}"
        else:
            val = f"{expr}{t}"
        set_val(expression, val)
