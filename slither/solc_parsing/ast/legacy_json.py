from typing import Callable

from slither.solc_parsing.exceptions import ParsingError
from slither.solc_parsing.ast.types import *  # lgtm[py/polluting-import]

"""
The legacy AST format is used by all versions of Solidity that Slither currently supports (i.e. >=0.4.0), but it must
be manually enabled for versions >=0.4.12. In general, all nodes contain the following properties:

id (int): internal node id, randomly generated
name (string): type of node
src (string): src offset

A node may also contain an array of children. This array is simply the concatenation of every child node and does
not contain nulls if a child node is unset. As a result, this results in ambiguities when parsing constructs like
a for loop.

A node may, for Solidity >=0.4.12, contain an optional attributes dictionary, which contains additional
properties about the node
"""


def _extract_base_props(raw: Dict) -> Dict:
    return {
        "src": raw.get("src", ""),
        "id": raw.get("id", -1),
    }


def _extract_decl_props(raw: Dict) -> Dict:
    return {
        **_extract_base_props(raw),
        "name": raw["attributes"]["name"],
        "canonical_name": raw.get("canonicalName", None),
        "visibility": raw["attributes"].get("visibility", "public"),
        "documentation": raw["attributes"].get("documentation", None),
        "referenced_declaration": raw["attributes"].get("referenced_delcaration", None),
    }


def _extract_expr_props(raw: Dict) -> Dict:
    return {
        **_extract_base_props(raw),
        "type_str": raw.get("attributes", {}).get("type", None),
        "constant": raw.get("isConstant", False),  # Identifier doesn't expose this
        "pure": raw.get("isPure", False),  # Identifier doesn't expose this
    }


def parse_emit_statement(raw: Dict) -> EmitStatement:
    event_call_parsed = parse(raw["children"][0])
    assert isinstance(event_call_parsed, FunctionCall)

    return EmitStatement(event_call=event_call_parsed, **_extract_base_props(raw))


def parse_variable_definition_statement(raw: Dict) -> VariableDeclarationStatement:
    """
    children:
        VariableDeclaration[]
        Expression?
    """
    parsed_children: List[Optional[VariableDeclaration]] = []
    for child in raw["children"][:-1]:
        child_parsed = parse(child)
        assert isinstance(child_parsed, VariableDeclaration)
        parsed_children.append(child_parsed)

    initial_value = None
    last_child = parse(raw["children"][-1])
    if isinstance(last_child, VariableDeclaration):
        parsed_children.append(last_child)
    else:
        initial_value = last_child
        assert isinstance(initial_value, Expression)

    return VariableDeclarationStatement(
        variables=parsed_children, initial_value=initial_value, **_extract_base_props(raw)
    )


def parse_expression_statement(raw: Dict) -> ExpressionStatement:
    """
    children:
        Expression
    """

    expression_parsed = parse(raw["children"][0])
    assert isinstance(expression_parsed, Expression)

    return ExpressionStatement(expression=expression_parsed, **_extract_base_props(raw))


def parse_conditional(raw: Dict) -> Conditional:
    true_expr_parsed = parse(raw["children"][0])
    assert isinstance(true_expr_parsed, Expression)

    false_expr_parsed = parse(raw["children"][1])
    assert isinstance(false_expr_parsed, Expression)

    cond_parsed = parse(raw["children"][2])
    assert isinstance(cond_parsed, Expression)

    return Conditional(
        condition=cond_parsed,
        true_expr=true_expr_parsed,
        false_expr=false_expr_parsed,
        **{**_extract_expr_props(raw), "type_str": "bool"},
    )


def parse_assignment(raw: Dict) -> Assignment:
    """
    children:
        left (Expression)
        right (Expression)

    attributes:
        operator (string)
        type (string)
    """

    left = parse(raw["children"][0])
    assert isinstance(left, Expression)

    right = parse(raw["children"][1])
    assert isinstance(right, Expression)

    return Assignment(
        left=left, operator=raw["attributes"]["operator"], right=right, **_extract_expr_props(raw)
    )


def parse_tuple_expression(raw: Dict) -> TupleExpression:
    """
    children:
        (Expression?)[]
    """
    # For expressions like (a,,c) = (1,2,3)
    # the AST provides only two children in the left side.
    # We check the type provided (tuple(uint256,,uint256))
    # to determine that there is an empty variable.
    # Otherwise, we would not be able to determine
    # that a = 1, c = 3, and 2 is lost.
    children_parsed: List[Optional[Expression]] = []
    if "children" not in raw:
        for component in raw["attributes"]["components"]:
            if component:
                child_parsed = parse(component)
                assert isinstance(child_parsed, Expression)

                children_parsed.append(child_parsed)
            else:
                children_parsed.append(None)
    else:
        for child in raw["children"]:
            if child:
                child_parsed = parse(child)
                assert isinstance(child_parsed, Expression)

                children_parsed.append(child_parsed)
            else:
                children_parsed.append(None)
    # TODO Add none for empty tuple items
    # if 'attributes' in attrs:
    #     if 'type' in attrs['attributes']:
    #         t = attrs['attributes']['type']
    #         if ',,' in t or '(,' in t or ',)' in t:
    #             t = t[len('tuple(') : -1]
    #             elems = t.split(',')
    #             for idx, _ in enumerate(elems):
    #                 if elems[idx] == '':
    #                     children_parsed.insert(idx, None)

    return TupleExpression(
        components=children_parsed,
        is_array=False,
        **{**_extract_expr_props(raw), "type_str": "tuple()"},
    )


def parse_unary_operation(raw: Dict) -> UnaryOperation:
    expression_parsed = parse(raw["children"][0])
    assert isinstance(expression_parsed, Expression)

    return UnaryOperation(
        operator=raw["attributes"]["operator"],
        expression=expression_parsed,
        is_prefix=raw["attributes"]["prefix"],
        **_extract_expr_props(raw),
    )


def parse_binary_operation(raw: Dict) -> BinaryOperation:
    left_parsed = parse(raw["children"][0])
    right_parsed = parse(raw["children"][1])

    assert isinstance(left_parsed, Expression)
    assert isinstance(right_parsed, Expression)

    return BinaryOperation(
        left=left_parsed,
        operator=raw["attributes"]["operator"],
        right=right_parsed,
        **_extract_expr_props(raw),
    )


def parse_function_call(raw: Dict) -> FunctionCall:
    attrs = raw["attributes"]

    if "isStructConstructorCall" in attrs:
        # >= 0.4.12
        if attrs["isStructConstructorCall"]:
            kind = "structConstructorCall"
        else:
            kind = "typeConversion" if attrs["type_conversion"] else "functionCall"
    else:
        # >= 0.4.0
        if attrs["type_conversion"]:
            kind = "typeConversion"
        elif attrs["type"].startswith("struct "):
            kind = "structConstructorCall"
        else:
            kind = "functionCall"

    if "names" in attrs:
        names = attrs["names"]
    else:
        names = []

    call_parsed = parse(raw["children"][0])
    assert isinstance(call_parsed, Expression)

    args_parsed: List[Expression] = []
    for child in raw["children"][1:]:
        child_parsed = parse(child)
        assert isinstance(child_parsed, Expression)
        args_parsed.append(child_parsed)

    return FunctionCall(
        kind=kind,
        expression=call_parsed,
        names=names,
        arguments=args_parsed,
        **_extract_expr_props(raw),
    )


def parse_function_call_options(raw: Dict) -> FunctionCallOptions:
    expression_parsed = parse(raw["children"][0])
    assert isinstance(expression_parsed, Expression)

    names = raw["attributes"]["names"]
    assert isinstance(names, list)
    for name in names:
        assert isinstance(name, str)

    options_parsed: List[Expression] = []
    for child in raw["children"][1:]:
        child_parsed = parse(child)
        assert isinstance(child_parsed, Expression)
        options_parsed.append(child_parsed)

    return FunctionCallOptions(
        expression=expression_parsed,
        names=names,
        options=options_parsed,
        **_extract_expr_props(raw),
    )


def parse_new_expression(raw: Dict) -> NewExpression:
    typename_parsed = parse(raw["children"][0])
    assert isinstance(typename_parsed, TypeName)

    return NewExpression(typename=typename_parsed, **_extract_expr_props(raw))


def parse_member_access(raw: Dict) -> MemberAccess:
    expr_parsed = parse(raw["children"][0])
    assert isinstance(expr_parsed, Expression)

    return MemberAccess(
        expression=expr_parsed,
        member_name=raw["attributes"]["member_name"],
        **_extract_expr_props(raw),
    )


def parse_while_statement_internal(raw: Dict, is_do_while: bool) -> WhileStatement:
    """
    condition (Expression)
    body (Statement)
    """

    condition_parsed = parse(raw["children"][0])
    assert isinstance(condition_parsed, Expression)

    body_parsed = parse(raw["children"][1])
    assert isinstance(body_parsed, Statement)

    return WhileStatement(
        condition=condition_parsed,
        body=body_parsed,
        is_do_while=is_do_while,
        **_extract_base_props(raw),
    )


def parse_while_statement(raw: Dict) -> WhileStatement:
    return parse_while_statement_internal(raw, False)


def parse_do_while_statement(raw: Dict) -> WhileStatement:
    return parse_while_statement_internal(raw, True)


def parse_for_statement(raw: Dict) -> ForStatement:
    # if we're using an old version of solc (anything below and including 0.4.11) or if the user
    # explicitly disabled compact ast, we might need to make some best-effort guesses
    children = raw["children"]

    # there should always be at least one, and never more than 4, children
    assert 1 <= len(children) <= 4

    # the last element of the children array must be the body, since it's mandatory
    # however, it might be a single expression
    body = children[-1]

    if len(children) == 4:
        # handle the first trivial case - if there are four children we know exactly what they are
        pre, cond, post = children[0], children[1], children[2]
    elif len(children) == 1:
        # handle the second trivial case - if there is only one child we know there are no expressions
        pre, cond, post = None, None, None
    else:
        attributes = raw.get("attributes", None)

        def has_hint(key):
            return key in attributes and not attributes[key]

        if attributes and any(
            map(
                has_hint,
                ["condition", "initializationExpression", "loopExpression"],
            )
        ):
            # if we have attribute hints, rely on those

            if len(children) == 2:
                # we're missing two expressions, find the one we have
                if not has_hint("initializationExpression"):
                    pre, cond, post = children[0], None, None
                elif not has_hint("condition"):
                    pre, cond, post = None, children[0], None
                else:  # if not has_hint('loopExpression'):
                    pre, cond, post = None, None, children[0]
            else:
                # we're missing one expression, figure out what it is
                if has_hint("initializationExpression"):
                    pre, cond, post = None, children[0], children[1]
                elif has_hint("condition"):
                    pre, cond, post = children[0], None, children[1]
                else:  # if has_hint('loopExpression'):
                    pre, cond, post = children[0], children[1], None
        else:
            # we don't have attribute hints, and it's literally impossible to be 100% accurate here
            # let's just try our best

            # the pre statement is a simple statement, and can only be one of the following nodes:
            #   variable declaration, expression statement
            #
            # the condition statement is an expression, and can only be one of the following nodes:
            #   assignment, conditional, binary, unary, new, indexaccess, memberaccess, functioncall,
            #   literal, identifier, tuple, elementary type name
            # however, the condition statement must also be convertible to a boolean
            #
            # the post statement is an expression statement, and can only be one of the following nodes:
            #    expression statement

            first_parsed = parse(children[0])
            second_parsed = parse(children[1])

            # VariableDefinitionStatement is used by solc 0.4.0-0.4.6
            # it's changed in 0.4.7 to VariableDeclarationStatement
            if isinstance(first_parsed, VariableDeclarationStatement):
                # only the pre statement can be a variable declaration

                if len(children) == 2:
                    # only one child apart from body, it must be pre
                    pre, cond, post = children[0], None, None
                else:
                    # more than one child, figure out which one is the cond
                    if isinstance(second_parsed, ExpressionStatement):
                        # only the post can be an expression statement
                        pre, cond, post = children[0], None, children[1]
                    else:
                        # similarly, the post cannot be anything other than an expression statement
                        pre, cond, post = children[0], children[1], None
            elif isinstance(first_parsed, ExpressionStatement):
                # the first element can either be pre or post

                if len(children) == 2:
                    # this is entirely ambiguous, so apply a very dumb heuristic:
                    # if the statement is closer to the start of the body, it's probably the post
                    # otherwise, it's probably the pre
                    # this will work in all cases where the formatting isn't completely borked

                    node_len = int(children[0]["src"].split(":")[1])

                    node_start = int(children[0]["src"].split(":")[0])
                    node_end = node_start + node_len

                    for_start = int(raw["src"].split(":")[0]) + 3  # trim off the 'for'
                    body_start = int(body["src"].split(":")[0])

                    dist_start = node_start - for_start
                    dist_end = body_start - node_end
                    if dist_start > dist_end:
                        pre, cond, post = None, None, children[0]
                    else:
                        pre, cond, post = children[0], None, None
                else:
                    # more than one child, we must be the pre
                    pre, cond, post = children[0], children[1], None
            else:
                # the first element must be the cond

                if len(children) == 2:
                    pre, cond, post = None, children[0], None
                else:
                    pre, cond, post = None, children[0], children[1]

    pre_parsed = parse(pre) if pre else None
    assert pre is None or isinstance(pre_parsed, Statement)

    cond_parsed = parse(cond) if cond else None
    assert cond is None or isinstance(cond_parsed, Expression)

    post_parsed = parse(post) if post else None
    assert post is None or isinstance(post_parsed, ExpressionStatement)

    body_parsed = parse(body)
    assert isinstance(body_parsed, Statement)

    return ForStatement(
        init=pre_parsed,
        cond=cond_parsed,
        loop=post_parsed,
        body=body_parsed,
        **_extract_base_props(raw),
    )


def parse_continue(raw: Dict) -> Continue:
    return Continue(**_extract_base_props(raw))


def parse_break(raw: Dict) -> Break:
    return Break(**_extract_base_props(raw))


def parse_throw(raw: Dict) -> Throw:
    return Throw(**_extract_base_props(raw))


def parse_source_unit(raw: Dict) -> SourceUnit:
    children_parsed: List[ASTNode] = []
    if "children" in raw:
        for child in raw["children"]:
            children_parsed.append(parse(child))
    return SourceUnit(nodes=children_parsed, **_extract_base_props(raw))


def parse_pragma_directive(raw: Dict) -> PragmaDirective:
    return PragmaDirective(literals=raw["attributes"]["literals"], **_extract_base_props(raw))


def parse_import_directive(raw: Dict) -> ImportDirective:

    attrs = raw["attributes"]
    alias = None
    if "unitAlias" in attrs and attrs["unitAlias"]:
        alias = UnitAlias(attrs["unitAlias"])

    symbol_aliases = None
    if "symbolAliases" in attrs and isinstance(attrs["symbolAliases"], dict):
        symbol_aliases = attrs["symbolAliases"]

    return ImportDirective(
        path=attrs["absolutePath"],
        unit_alias=alias,
        symbol_aliases=symbol_aliases,
        **_extract_base_props(raw),
    )


def parse_contract_definition(raw: Dict) -> ContractDefinition:
    attrs = raw["attributes"]

    if "contractKind" in attrs:
        # >=0.4.12
        kind = attrs["contractKind"]
    else:
        # <0.4.12
        if attrs["isLibrary"]:
            kind = "library"
        elif attrs["fullyImplemented"]:
            kind = "contract"
        else:
            kind = "interface"

    linearized = attrs["linearizedBaseContracts"]

    base_contracts = []
    nodes = []
    if "children" in raw:
        for child in raw["children"]:
            child_parsed = parse(child)
            if isinstance(child_parsed, InheritanceSpecifier):
                base_contracts.append(child_parsed)
            else:
                nodes.append(child_parsed)

    return ContractDefinition(
        kind=kind,
        linearized_base_contracts=linearized,
        base_contracts=base_contracts,
        nodes=nodes,
        **_extract_decl_props(raw),
    )


def parse_inheritance_specifier(raw: Dict) -> InheritanceSpecifier:
    basename_parsed = parse(raw["children"][0])
    assert isinstance(basename_parsed, UserDefinedTypeName)

    if len(raw["children"]) > 1:
        args_parsed = []
        for child in raw["children"][1:]:
            child_parsed = parse(child)
            assert isinstance(child_parsed, Expression)
            args_parsed.append(child_parsed)
    else:
        args_parsed = None

    return InheritanceSpecifier(
        basename=basename_parsed, args=args_parsed, **_extract_base_props(raw)
    )


def parse_using_for_directive(raw: Dict) -> UsingForDirective:
    library = parse(raw["children"][0])
    assert isinstance(library, UserDefinedTypeName)

    typename_parsed = WildCardTypeName(name="*", src="", id=-1)
    if len(raw["children"]) > 1:
        typename_parsed = parse(raw["children"][1])
        assert isinstance(typename_parsed, TypeName)

    return UsingForDirective(
        library=library,
        typename=typename_parsed,
        function_list=None,
        is_global=False,
        **_extract_base_props(raw),
    )


def parse_struct_definition(raw: Dict) -> StructDefinition:

    members_parsed: List[VariableDeclaration] = []
    for child in raw["children"]:
        child_parsed = parse(child)
        assert isinstance(child_parsed, VariableDeclaration)
        members_parsed.append(child_parsed)

    return StructDefinition(members=members_parsed, **_extract_decl_props(raw))


def parse_enum_definition(raw: Dict) -> EnumDefinition:
    attrs = raw["attributes"]

    members_parsed: List[EnumValue] = []
    for child in raw["children"]:
        child_parsed = parse(child)
        assert isinstance(child_parsed, EnumValue)
        members_parsed.append(child_parsed)

    return EnumDefinition(
        members=members_parsed, **{**_extract_decl_props(raw), "visibility": None}
    )


def parse_enum_value(raw: Dict) -> EnumValue:
    return EnumValue(**_extract_decl_props(raw))


def parse_function_definition(raw: Dict) -> FunctionDefinition:
    attrs = raw["attributes"]
    if "stateMutability" in attrs:
        # >=0.4.16
        mutability = attrs["stateMutability"]
    elif "payable" in attrs:
        # >=0.4.5
        mutability = "payable" if attrs["payable"] else "nonpayable"
    else:
        # >=0.4.0
        """
        as it turns out, constant functions can do non-constant things, so mark it as payable so err on the side
        of more detectors triggering
        """
        mutability = "payable"

    if "kind" in attrs:
        # >= 0.5.0
        kind = attrs["kind"]
    elif "isConstructor" in attrs and attrs["isConstructor"]:
        # >= 0.4.12
        kind = "constructor"
    else:
        # >= 0.4.0
        kind = "fallback" if attrs["name"] == "" else "function"

    assert len(raw["children"]) >= 2

    # From Solidity 0.6.3 to 0.6.10 (included) the
    # comment above a function might be added in the children
    # of an function for the legacy ast
    params_iter = iter(
        [parse(child) for child in raw["children"] if child["name"] == "ParameterList"]
    )

    params = next(params_iter)
    assert isinstance(params, ParameterList)
    rets = next(params_iter)
    assert isinstance(rets, ParameterList)

    modifiers_parsed: List[ModifierInvocation] = []
    body = None
    for child in raw["children"][2:]:
        child_parsed = parse(child)
        if child["name"] == "Block":
            assert isinstance(child_parsed, Block)
            body = child_parsed
        elif child["name"] == "ModifierInvocation":
            assert isinstance(child_parsed, ModifierInvocation)
            modifiers_parsed.append(child_parsed)

    return FunctionDefinition(
        mutability=mutability,
        kind=kind,
        modifiers=modifiers_parsed,
        body=body,
        params=params,
        rets=rets,
        **_extract_decl_props(raw),
    )


def parse_parameter_list(raw: Dict) -> ParameterList:
    """
    children:
        (VariableDeclaration?)[]
    """

    parameters_parsed: List[Optional[VariableDeclaration]] = []

    for child in raw["children"]:
        if child:
            child_parsed = parse(child)
            assert isinstance(child_parsed, VariableDeclaration)

            parameters_parsed.append(child_parsed)
        else:
            parameters_parsed.append(None)

    return ParameterList(params=parameters_parsed, **_extract_base_props(raw))


def parse_elementary_type_name(raw: Dict) -> ElementaryTypeName:
    attrs = raw["attributes"]
    if "stateMutability" in attrs:
        # >=0.5.0
        mutability = attrs["stateMutability"]
    else:
        # >=0.4.0
        mutability = "payable" if attrs["name"] == "address" else None

    return ElementaryTypeName(name=attrs["name"], mutability=mutability, **_extract_base_props(raw))


def parse_user_defined_type_name(raw: Dict) -> UserDefinedTypeName:
    name = raw["attributes"]["name"]
    if "referencedDeclaration" in raw["attributes"]:
        # >= 0.4.12
        referenced_declaration = raw["attributes"]["referencedDeclaration"]
    else:
        referenced_declaration = None
    type_name_key = "type" if "type" in raw["attributes"] else "name"
    type_str = raw["attributes"][type_name_key]

    return UserDefinedTypeName(
        name=name,
        referenced_declaration=referenced_declaration,
        type_str=type_str,
        **_extract_base_props(raw),
    )


def parse_function_type_name(raw: Dict) -> FunctionTypeName:
    params_parsed = parse(raw["children"][0])
    assert isinstance(params_parsed, ParameterList)

    rets_parsed = parse(raw["children"][1])
    assert isinstance(rets_parsed, ParameterList)

    attrs = raw["attributes"]
    visibility = attrs["visibility"] if "visibility" in attrs else "public"
    mutability = attrs["stateMutability"] if "stateMutability" in attrs else None

    if "public" in attrs:
        visibility = "public" if attrs["public"] else "private"

    if "payable" in attrs:
        mutability = attrs["payable"]

    return FunctionTypeName(
        params=params_parsed,
        rets=rets_parsed,
        visibility=visibility,
        mutability=mutability,
        **_extract_base_props(raw),
    )


def parse_mapping(raw: Dict) -> Mapping:
    key_parsed = parse(raw["children"][0])
    assert isinstance(key_parsed, TypeName)

    value_parsed = parse(raw["children"][1])
    assert isinstance(value_parsed, TypeName)

    return Mapping(key=key_parsed, value=value_parsed, **_extract_base_props(raw))


def parse_array_type_name(raw: Dict) -> ArrayTypeName:
    base_parsed = parse(raw["children"][0])
    assert isinstance(base_parsed, TypeName)

    len_parsed = None
    if len(raw["children"]) > 1:
        len_parsed = parse(raw["children"][1])
        assert isinstance(len_parsed, Expression)

    return ArrayTypeName(base=base_parsed, len=len_parsed, **_extract_base_props(raw))


def parse_inline_assembly(raw: Dict) -> InlineAssembly:
    operations = None
    if "attributes" in raw:
        if "operations" in raw["attributes"]:
            # >=0.4.12
            operations = raw["attributes"]["operations"]

    return InlineAssembly(ast=operations, **_extract_base_props(raw))


def parse_block(raw: Dict) -> Block:
    """
    children:
        Statement[]
    """

    parsed_statements: List[Statement] = []
    for statement in raw["children"]:
        parsed_statement = parse(statement)
        assert isinstance(parsed_statement, Statement)
        parsed_statements.append(parsed_statement)

    return Block(statements=parsed_statements, **_extract_base_props(raw))


def parse_placeholder_statement(raw: Dict) -> PlaceholderStatement:
    return PlaceholderStatement(**_extract_base_props(raw))


def parse_if_statement(raw: Dict) -> IfStatement:
    condition_parsed = parse(raw["children"][0])
    assert isinstance(condition_parsed, Expression)

    true_body_parsed = parse(raw["children"][1])
    assert isinstance(true_body_parsed, Statement)

    false_body_parsed = None
    if len(raw["children"]) > 2:
        false_body_parsed = parse(raw["children"][2])
        assert isinstance(false_body_parsed, Statement)

    return IfStatement(
        condition=condition_parsed,
        true_body=true_body_parsed,
        false_body=false_body_parsed,
        **_extract_base_props(raw),
    )


def parse_return(raw: Dict) -> Return:
    """
    children:
        Expression?
    """

    expr_parsed = None
    if len(raw["children"]) > 0:
        expr_parsed = parse(raw["children"][0])
        assert isinstance(expr_parsed, Expression)

    return Return(expression=expr_parsed, **_extract_base_props(raw))


def parse_variable_declaration(raw: Dict) -> VariableDeclaration:
    attrs = raw["attributes"]

    mutability = "mutable"
    if "constant" in attrs:
        # >=0.4.11
        mutability = "constant" if attrs["constant"] else "mutable"
    if "mutability" in attrs:
        mutability = attrs["mutability"]

    typename = None
    if raw["children"]:
        typename = parse(raw["children"][0])
        assert isinstance(typename, TypeName)

    value = None
    if len(raw["children"]) > 1:
        value = parse(raw["children"][1])
        assert isinstance(value, Expression)

    indexed = attrs["indexed"] if "indexed" in attrs else None

    if "storageLocation" in attrs:
        # >= 0.4.11
        storage_location = attrs["storageLocation"]
    else:
        # >= 0.4.0
        if "memory" in attrs["type"]:
            storage_location = "memory"
        elif "storage" in attrs["type"]:
            storage_location = "storage"
        else:
            storage_location = "default"

    return VariableDeclaration(
        typename=typename,
        value=value,
        type_str=attrs["type"],
        mutability=mutability,
        indexed=indexed,
        location=storage_location,
        **_extract_decl_props(raw),
    )


def parse_modifier_definition(raw: Dict) -> ModifierDefinition:
    params = parse(raw["children"][0])
    assert isinstance(params, ParameterList)

    body = None
    if len(raw["children"]) > 1:
        body = parse(raw["children"][1])
        assert isinstance(body, Block)

    return ModifierDefinition(
        body=body,
        params=params,
        **{**_extract_decl_props(raw), "rets": None, "visibility": "internal"},
    )


def parse_modifier_invocation(raw: Dict) -> ModifierInvocation:
    name = parse(raw["children"][0])
    assert isinstance(name, Identifier)

    args_parsed: List[Expression] = []
    for child in raw["children"][1:]:
        child_parsed = parse(child)
        assert isinstance(child_parsed, Expression)
        args_parsed.append(child_parsed)

    return ModifierInvocation(modifier=name, args=args_parsed, **_extract_base_props(raw))


def parse_event_definition(raw: Dict) -> EventDefinition:
    # From Solidity 0.6.3 to 0.6.10 (included) the
    # comment above a event might be added in the children
    # of an event for the legacy ast
    for elem in raw["children"]:
        if elem["name"] == "ParameterList":
            params = parse(elem)
            assert isinstance(params, ParameterList)

    attrs = raw["attributes"]
    anonymous = attrs["anonymous"] if "anonymous" in attrs else False

    return EventDefinition(
        anonymous=anonymous,
        params=params,
        **{**_extract_decl_props(raw), "visibility": None, "rets": None},
    )


def parse_index_access(raw: Dict) -> IndexAccess:
    base_parsed = parse(raw["children"][0])
    assert isinstance(base_parsed, Expression)

    index_parsed = None
    if len(raw["children"]) > 1:
        index_parsed = parse(raw["children"][1])
        assert isinstance(index_parsed, Expression)

    return IndexAccess(base=base_parsed, index=index_parsed, **_extract_expr_props(raw))


def parse_index_range_access(raw: Dict) -> IndexRangeAccess:
    base = parse(raw["children"][0])
    assert isinstance(base, Expression)

    start = parse(raw["children"][1])
    assert isinstance(start, Expression)

    end = None
    if len(raw["children"]) > 2:
        end = parse(raw["children"][2])
        assert isinstance(end, Expression)

    return IndexRangeAccess(base=base, start=start, end=end, **_extract_expr_props(raw))


def parse_identifier(raw: Dict) -> Identifier:
    """
    attributes:
        type (string)
        value (string)
    """
    referenced_declaration = None
    if "referencedDeclaration" in raw["attributes"]:
        referenced_declaration = raw["attributes"]["referencedDeclaration"]
        assert isinstance(referenced_declaration, int)
    return Identifier(
        name=raw["attributes"]["value"],
        referenced_declaration=referenced_declaration,
        **_extract_expr_props(raw),
    )


def parse_elementary_type_name_expression(raw: Dict) -> ElementaryTypeNameExpression:
    if "children" in raw:
        typename_parsed = parse(raw["children"][0])
        assert isinstance(typename_parsed, ElementaryTypeName)
    else:
        typename_parsed = ElementaryTypeName(
            name=raw["attributes"]["value"], mutability=None, **_extract_base_props(raw)
        )
    return ElementaryTypeNameExpression(typename=typename_parsed, **_extract_expr_props(raw))


def parse_literal(raw: Dict) -> Literal:
    attrs = raw["attributes"]
    subdenomination = None
    if "subdenomination" in attrs:
        subdenomination = attrs["subdenomination"]
    return Literal(
        kind=attrs["token"],
        value=attrs["value"],
        hex_value=attrs["hexvalue"],
        subdenomination=subdenomination,
        **_extract_expr_props(raw),
    )


def parse_unsupported(raw: Dict) -> ASTNode:
    raise ParsingError(
        "unsupported legacy json node",
        raw["name"],
        raw.keys(),
        [node["name"] for node in raw["children"]] if "children" in raw else [],
        raw,
    )


def parse(raw: Dict) -> ASTNode:
    try:
        return PARSERS.get(raw["name"], parse_unsupported)(raw)
    except ParsingError as e:
        raise e
    except Exception as e:
        raise ParsingError("failed to parse legacy json node", raw["name"], e, raw.keys(), raw)


PARSERS: Dict[str, Callable[[Dict], ASTNode]] = {
    "SourceUnit": parse_source_unit,
    "PragmaDirective": parse_pragma_directive,
    "ImportDirective": parse_import_directive,
    "ContractDefinition": parse_contract_definition,
    "InheritanceSpecifier": parse_inheritance_specifier,
    "UsingForDirective": parse_using_for_directive,
    "StructDefinition": parse_struct_definition,
    "EnumDefinition": parse_enum_definition,
    "EnumValue": parse_enum_value,
    "ParameterList": parse_parameter_list,
    "FunctionDefinition": parse_function_definition,
    "VariableDeclaration": parse_variable_declaration,
    "ModifierDefinition": parse_modifier_definition,
    "ModifierInvocation": parse_modifier_invocation,
    "EventDefinition": parse_event_definition,
    "ElementaryTypeName": parse_elementary_type_name,
    "UserDefinedTypeName": parse_user_defined_type_name,
    "FunctionTypeName": parse_function_type_name,
    "Mapping": parse_mapping,
    "ArrayTypeName": parse_array_type_name,
    "InlineAssembly": parse_inline_assembly,
    "Block": parse_block,
    "PlaceholderStatement": parse_placeholder_statement,
    "IfStatement": parse_if_statement,
    # 'TryCatchClause': parse_try_catch_clause,
    # 'TryStatement': parse_try_statement,
    "WhileStatement": parse_while_statement,
    "DoWhileStatement": parse_do_while_statement,
    "ForStatement": parse_for_statement,
    "Continue": parse_continue,
    "Break": parse_break,
    "Return": parse_return,
    "Throw": parse_throw,
    "EmitStatement": parse_emit_statement,
    "VariableDeclarationStatement": parse_variable_definition_statement,  # >=0.4.7
    "VariableDefinitionStatement": parse_variable_definition_statement,  # <=0.4.6
    "ExpressionStatement": parse_expression_statement,
    "Conditional": parse_conditional,
    "Assignment": parse_assignment,
    "TupleExpression": parse_tuple_expression,
    "UnaryOperation": parse_unary_operation,
    "BinaryOperation": parse_binary_operation,
    "FunctionCall": parse_function_call,
    "FunctionCallOptions": parse_function_call_options,
    "NewExpression": parse_new_expression,
    "MemberAccess": parse_member_access,
    "IndexAccess": parse_index_access,
    "IndexRangeAccess": parse_index_range_access,
    "Identifier": parse_identifier,
    "ElementaryTypeNameExpression": parse_elementary_type_name_expression,
    "ElementaryTypenameExpression": parse_elementary_type_name_expression,
    "Literal": parse_literal,
}
