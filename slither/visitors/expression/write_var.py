from slither.visitors.expression.expression import ExpressionVisitor

key = "WriteVar"


def get(expression):
    val = expression.context[key]
    # we delete the item to reduce memory use
    del expression.context[key]
    return val


def set_val(expression, val):
    expression.context[key] = val


class WriteVar(ExpressionVisitor):
    def result(self):
        if self._result is None:
            self._result = list(set(get(self.expression)))
        return self._result

    def _post_binary_operation(self, expression):
        left = get(expression.expression_left)
        right = get(expression.expression_right)
        val = left + right
        if expression.is_lvalue:
            val += [expression]
        set_val(expression, val)

    def _post_call_expression(self, expression):
        called = get(expression.called)
        args = [get(a) for a in expression.arguments if a]
        args = [item for sublist in args for item in sublist]
        val = called + args
        if expression.is_lvalue:
            val += [expression]
        set_val(expression, val)

    def _post_conditional_expression(self, expression):
        if_expr = get(expression.if_expression)
        else_expr = get(expression.else_expression)
        then_expr = get(expression.then_expression)
        val = if_expr + else_expr + then_expr
        if expression.is_lvalue:
            val += [expression]
        set_val(expression, val)

    def _post_assignement_operation(self, expression):
        left = get(expression.expression_left)
        right = get(expression.expression_right)
        val = left + right
        if expression.is_lvalue:
            val += [expression]
        set_val(expression, val)

    def _post_elementary_type_name_expression(self, expression):
        set_val(expression, [])

    # save only identifier expression
    def _post_identifier(self, expression):
        if expression.is_lvalue:
            set_val(expression, [expression])
        else:
            set_val(expression, [])

    #        if isinstance(expression.value, Variable):
    #            set_val(expression, [expression.value])
    #        else:
    #            set_val(expression, [])

    def _post_index_access(self, expression):
        left = get(expression.expression_left)
        right = get(expression.expression_right)
        val = left + right
        if expression.is_lvalue:
            #       val += [expression]
            val += [expression.expression_left]
        #       n = expression.expression_left
        # parse all the a.b[..].c[..]
        #      while isinstance(n, (IndexAccess, MemberAccess)):
        #          if isinstance(n, IndexAccess):
        #              val += [n.expression_left]
        #              n = n.expression_left
        #          else:
        #              val += [n.expression]
        #              n = n.expression
        set_val(expression, val)

    def _post_literal(self, expression):
        set_val(expression, [])

    def _post_member_access(self, expression):
        expr = get(expression.expression)
        val = expr
        if expression.is_lvalue:
            val += [expression]
            val += [expression.expression]
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
        if expression.is_lvalue:
            val += [expression]
        set_val(expression, val)

    def _post_type_conversion(self, expression):
        expr = get(expression.expression)
        val = expr
        if expression.is_lvalue:
            val += [expression]
        set_val(expression, val)

    def _post_unary_operation(self, expression):
        expr = get(expression.expression)
        val = expr
        if expression.is_lvalue:
            val += [expression]
        set_val(expression, val)
