
from slither.visitors.expression.expression import ExpressionVisitor

def get(expression):
    val = expression.context['ExpressionPrinter']
    # we delete the item to reduce memory use
    del expression.context['ExpressionPrinter']
    return val

def set_val(expression, val):
    expression.context['ExpressionPrinter'] = val

class ExpressionPrinter(ExpressionVisitor):

    def result(self):
        if not self._result:
            self._result = get(self.expression)
        return self._result

    def _post_assignement_operation(self, expression):
        left = get(expression.expression_left)
        right = get(expression.expression_right)
        val = "{} {} {}".format(left, expression.type_str, right)
        set_val(expression, val)

    def _post_binary_operation(self, expression):
        left = get(expression.expression_left)
        right = get(expression.expression_right)
        val = "{} {} {}".format(left,  expression.type_str, right)
        set_val(expression, val)

    def _post_call_expression(self, expression):
        called = get(expression.called)
        arguments = [get(x) for x in expression.arguments if x]
        val = "{}({})".format(called, ','.join(arguments))
        set_val(expression, val)

    def _post_conditional_expression(self, expression):
        if_expr = get(expression.if_expression)
        else_expr = get(expression.else_expression)
        then_expr = get(expression.then_expression)
        val = "if {} then {} else {}".format(if_expr, else_expr, then_expr)
        set_val(expression, val)

    def _post_elementary_type_name_expression(self, expression):
        set_val(expression, str(expression.type))

    def _post_identifier(self, expression):
        set_val(expression, str(expression.value))

    def _post_index_access(self, expression):
        left = get(expression.expression_left)
        right = get(expression.expression_right)
        val = "{}[{}]".format(left, right)
        set_val(expression, val)

    def _post_literal(self, expression):
        set_val(expression, str(expression.value))

    def _post_member_access(self, expression):
        expr = get(expression.expression)
        member_name = str(expression.member_name)
        val = "{}.{}".format(expr, member_name)
        set_val(expression, val)

    def _post_new_array(self, expression):
        array = str(expression.array_type)
        depth = expression.depth
        val = "new {}{}".format(array, '[]'*depth)
        set_val(expression, val)

    def _post_new_contract(self, expression):
        contract = str(expression.contract_name)
        val = "new {}".format(contract)
        set_val(expression, val)

    def _post_new_elementary_type(self, expression):
        t = str(expression.type)
        val = "new {}".format(t)
        set_val(expression, val)

    def _post_tuple_expression(self, expression):
        expressions = [get(e) for e in expression.expressions if e]
        val = "({})".format(','.join(expressions))
        set_val(expression, val)

    def _post_type_conversion(self, expression):
        t = str(expression.type)
        expr = get(expression.expression)
        val = "{}({})".format(t, expr)
        set_val(expression, val)

    def _post_unary_operation(self, expression):
        t = str(expression.type)
        expr = get(expression.expression)
        if expression.is_prefix:
            val = "{}{}".format(t, expr)
        else:
            val = "{}{}".format(expr, t)
        set_val(expression, val)
