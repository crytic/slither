# Return the 'left' value of an expression

from slither.visitors.expression.expression import ExpressionVisitor

from slither.core.expressions.assignment_operation import AssignmentOperationType

from slither.core.variables.variable import Variable

key = 'LeftValue'

def get(expression):
    val = expression.context[key]
    # we delete the item to reduce memory use
    del expression.context[key]
    return val

def set_val(expression, val):
    expression.context[key] = val

class LeftValue(ExpressionVisitor):

    def result(self):
        if self._result is None:
            self._result = list(set(get(self.expression)))
        return self._result

    # overide index access visitor to explore only left part
    def _visit_index_access(self, expression):
        self._visit_expression(expression.expression_left)

    def _post_assignement_operation(self, expression):
        if expression.type != AssignmentOperationType.ASSIGN:
            left = get(expression.expression_left)
        else:
            left = []
        right = get(expression.expression_right)
        val = left + right
        set_val(expression, val)

    def _post_binary_operation(self, expression):
        left = get(expression.expression_left)
        right = get(expression.expression_right)
        val = left + right
        set_val(expression, val)

    def _post_call_expression(self, expression):
        called = get(expression.called)
        args = [get(a) for a in expression.arguments if a]
        args = [item for sublist in args for item in sublist]
        val = called + args
        set_val(expression, val)

    def _post_conditional_expression(self, expression):
        if_expr = get(expression.if_expression)
        else_expr = get(expression.else_expression)
        then_expr = get(expression.then_expression)
        val = if_expr + else_expr + then_expr
        set_val(expression, val)

    def _post_elementary_type_name_expression(self, expression):
        set_val(expression, [])

    # save only identifier expression
    def _post_identifier(self, expression):
        if isinstance(expression.value, Variable):
            set_val(expression, [expression.value])
#        elif isinstance(expression.value, SolidityInbuilt):
#            set_val(expression, [expression])
        else:
            set_val(expression, [])

    def _post_index_access(self, expression):
        left = get(expression.expression_left)
        val = left
        set_val(expression, val)

    def _post_literal(self, expression):
        set_val(expression, [])

    def _post_member_access(self, expression):
        expr = get(expression.expression)
        val = expr
        set_val(expression, val)

    def _post_new_array(self, expression):
        set_val(expression, [])

    def _post_new_contract(self, expression):
        set_val(expression, [])

    def _post_new_elementary_type(self, expression):
        set_val(expression, [])

    def _post_tuple_expression(self, expression):
        expressions = [get(e) for e in expression.expressions if e]
        val = [item for sublist in expressions for item in sublist]
        set_val(expression, val)

    def _post_type_conversion(self, expression):
        expr = get(expression.expression)
        val = expr
        set_val(expression, val)

    def _post_unary_operation(self, expression):
        expr = get(expression.expression)
        val = expr
        set_val(expression, val)
