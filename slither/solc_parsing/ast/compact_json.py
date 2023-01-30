from typing import Callable
from slither.solc_parsing.exceptions import ParsingError
from slither.solc_parsing.ast.types import *  # lgtm[py/polluting-import]

"""
The compact AST format was introduced in Solidity 0.4.12. In general, each node contains the following properties:

id (int): internal node id
nodeType (string): type of node
src (string): src offset

A node may also contain common properties depending on its type. All expressions, declarations, and calls share
similar properties, which are extracted below
"""


def _extract_base_props(raw: Dict) -> Dict:
    return {
        "src": raw["src"],
        "id": raw["id"],
    }


def _extract_expr_props(raw: Dict) -> Dict:
    return {
        **_extract_base_props(raw),
        "type_str": raw["typeDescriptions"]["typeString"],
        "constant": raw.get("isConstant", False),  # Identifier doesn't expose this
        "pure": raw.get("isPure", False),  # Identifier doesn't expose this
    }


def _extract_decl_props(raw: Dict) -> Dict:
    documentation = None
    if "documentation" in raw and raw["documentation"]:
        if "text" in raw["documentation"]:
            documentation = raw["documentation"]["text"]
        else:
            documentation = raw["documentation"]
        assert isinstance(documentation, str)

    return {
        **_extract_base_props(raw),
        "name": raw.get("name", None),
        "canonical_name": raw.get("canonicalName", ""),
        "visibility": raw.get("visibility", None),
        "documentation": documentation,
        "referenced_declaration": raw.get("referencedDeclaration", None),
    }


def _extract_call_props(raw: Dict) -> Dict:
    params = parse(raw["parameters"])

    if "returnParameters" in raw:
        rets = parse(raw["returnParameters"])
    else:
        rets = None

    return {
        **_extract_decl_props(raw),
        "params": params,
        "rets": rets,
    }


def parse_source_unit(raw: Dict) -> SourceUnit:
    nodes_parsed: List[ASTNode] = []

    for node in raw["nodes"]:
        nodes_parsed.append(parse(node))

    return SourceUnit(nodes=nodes_parsed, **_extract_base_props(raw))


def parse_identifier_path(raw: Dict) -> IdentifierPath:
    return IdentifierPath(**_extract_decl_props(raw))


def parse_user_defined_value_type_definition(raw: Dict) -> UserDefinedValueTypeDefinition:
    underlying_type = parse(raw["underlyingType"])
    assert isinstance(underlying_type, ElementaryTypeName)
    return UserDefinedValueTypeDefinition(
        underlying_type=underlying_type, alias=raw["name"], **_extract_decl_props(raw)
    )


def parse_pragma_directive(raw: Dict) -> PragmaDirective:
    return PragmaDirective(literals=raw["literals"], **_extract_base_props(raw))


def parse_import_directive(raw: Dict) -> ImportDirective:
    # # TODO investigate unitAlias in version < 0.7 and legacy ast
    # dedup
    alias = None
    if "unitAlias" in raw and raw["unitAlias"]:
        alias = UnitAlias(raw["unitAlias"])

    symbol_aliases = None
    if "symbolAliases" in raw and raw["symbolAliases"]:
        symbol_aliases = raw["symbolAliases"]

    return ImportDirective(
        path=raw["absolutePath"],
        unit_alias=alias,
        symbol_aliases=symbol_aliases,
        **_extract_base_props(raw),
    )


def parse_contract_definition(raw: Dict) -> ContractDefinition:
    nodes_parsed: List[ASTNode] = []
    for child in raw["nodes"]:
        nodes_parsed.append(parse(child))

    base_contracts: List[InheritanceSpecifier] = []
    for child in raw["baseContracts"]:
        child_parsed = parse(child)
        assert isinstance(child_parsed, InheritanceSpecifier)

        base_contracts.append(child_parsed)

    return ContractDefinition(
        kind=raw["contractKind"],
        linearized_base_contracts=raw["linearizedBaseContracts"],
        base_contracts=base_contracts,
        nodes=nodes_parsed,
        **_extract_decl_props(raw),
    )


def parse_inheritance_specifier(raw: Dict) -> InheritanceSpecifier:
    basename_parsed = parse(raw["baseName"])
    assert isinstance(basename_parsed, (UserDefinedTypeName, IdentifierPath))

    args_parsed = None
    if "arguments" in raw and raw["arguments"]:
        args_parsed = []
        for child in raw["arguments"]:
            child_parsed = parse(child)
            assert isinstance(child_parsed, Expression)
            args_parsed.append(child_parsed)

    return InheritanceSpecifier(
        basename=basename_parsed, args=args_parsed, **_extract_base_props(raw)
    )


def parse_using_for_directive(raw: Dict) -> UsingForDirective:
    library_name_parsed = None
    function_list = []
    if "libraryName" in raw:
        library_name_parsed = parse(raw["libraryName"])
        assert isinstance(library_name_parsed, (UserDefinedTypeName, IdentifierPath))
    else:
        assert "functionList" in raw
        for func in raw["functionList"]:
            parsed_func = parse(func["function"])
            assert isinstance(parsed_func, IdentifierPath)
            function_list.append(parsed_func)

    typename_parsed = WildCardTypeName(name="*", src="", id=-1)
    if "typeName" in raw and raw["typeName"]:
        typename_parsed = parse(raw["typeName"])
        assert isinstance(typename_parsed, TypeName)

    is_global = False
    if "global" in raw:
        is_global = raw["global"]

    return UsingForDirective(
        library=library_name_parsed,
        typename=typename_parsed,
        function_list=function_list,
        is_global=is_global,
        **_extract_base_props(raw),
    )


def parse_error_definition(raw: Dict) -> ErrorDefinition:
    return ErrorDefinition(
        params=parse_parameter_list(raw["parameters"]), **_extract_decl_props(raw)
    )


def parse_struct_definition(raw: Dict) -> StructDefinition:
    members_parsed: List[VariableDeclaration] = []
    for child in raw["members"]:
        child_parsed = parse(child)
        assert isinstance(child_parsed, VariableDeclaration)
        members_parsed.append(child_parsed)

    return StructDefinition(members=members_parsed, **_extract_decl_props(raw))


def parse_enum_definition(raw: Dict) -> EnumDefinition:
    members_parsed: List[EnumValue] = []
    for child in raw["members"]:
        child_parsed = parse(child)
        assert isinstance(child_parsed, EnumValue)
        members_parsed.append(child_parsed)

    return EnumDefinition(members=members_parsed, **_extract_decl_props(raw))


def parse_enum_value(raw: Dict) -> EnumValue:
    return EnumValue(**_extract_decl_props(raw))


def parse_parameter_list(raw: Dict) -> ParameterList:
    """
    parameters (VariableDeclaration[])
    """

    parameters_parsed = []
    for child in raw["parameters"]:
        child_parsed = parse(child)
        assert isinstance(child_parsed, VariableDeclaration)
        parameters_parsed.append(child_parsed)

    return ParameterList(params=parameters_parsed, **_extract_base_props(raw))


def parse_function_definition(raw: Dict) -> FunctionDefinition:
    body_parsed = None
    if "body" in raw and raw["body"]:
        body_parsed = parse(raw["body"])
        assert isinstance(body_parsed, Block)

    modifiers_parsed = []
    for child in raw["modifiers"]:
        child_parsed = parse(child)
        assert isinstance(child_parsed, ModifierInvocation)
        modifiers_parsed.append(child_parsed)

    if "stateMutability" in raw:
        # >=0.4.16
        mutability = raw["stateMutability"]
    elif "payable" in raw:
        # >=0.4.5
        mutability = "payable" if raw["payable"] else "nonpayable"
    else:
        raise ParsingError("don't know how to extract state mutability")

    if "kind" in raw:
        # >= 0.5.0
        kind = raw["kind"]
    elif "isConstructor" in raw and raw["isConstructor"]:
        # >= 0.4.12
        kind = "constructor"
    else:
        # >= 0.4.0
        kind = "fallback" if raw["name"] == "" else "function"

    return FunctionDefinition(
        mutability=mutability,
        kind=kind,
        modifiers=modifiers_parsed,
        body=body_parsed,
        **_extract_call_props(raw),
    )


def parse_variable_declaration(raw: Dict) -> VariableDeclaration:
    """
    name (string)
    typeName (ElementaryTypeName)
    constant (boolean)
    mutability (string)
    stateVariable (boolean)
    storageLocation (string)
    overrides (OverrideSpecifier[]?)
    visibility (string)
    value (Expression?)
    scope (int)
    typeDescriptions (TypeDescription)
    functionSelector (string): only if public state variable
    indexed (bool): only if event variable
    baseFunctions (int[]): only if overriding function
    """

    typename = None
    if raw["typeName"]:
        typename = parse(raw["typeName"])
        assert isinstance(typename, TypeName)

    value_parsed = None
    if "value" in raw and raw["value"]:
        value_parsed = parse(raw["value"])
        assert isinstance(value_parsed, Expression)

    indexed = raw["indexed"] if "indexed" in raw else None

    storage_location = raw["storageLocation"]

    mutability = "mutable"
    if "constant" in raw:
        # >=0.4.11
        mutability = "constant" if raw["constant"] else "mutable"
    if "mutability" in raw:
        mutability = raw["mutability"]

    return VariableDeclaration(
        typename=typename,
        value=value_parsed,
        type_str=raw["typeDescriptions"]["typeString"],
        mutability=mutability,
        indexed=indexed,
        location=storage_location,
        **_extract_decl_props(raw),
    )


def parse_modifier_definition(raw: Dict) -> ModifierDefinition:
    body_parsed = None
    if "body" in raw and raw["body"]:
        body_parsed = parse(raw["body"])
        assert isinstance(body_parsed, Block)

    return ModifierDefinition(body=body_parsed, **_extract_call_props(raw))


def parse_modifier_invocation(raw: Dict) -> ModifierInvocation:
    arguments_parsed: Optional[List[Expression]] = None
    if "arguments" in raw and raw["arguments"]:
        arguments_parsed = []
        for child in raw["arguments"]:
            child_parsed = parse(child)
            assert isinstance(child_parsed, Expression)
            arguments_parsed.append(child_parsed)

    name_parsed = parse(raw["modifierName"])
    assert isinstance(name_parsed, (Identifier, IdentifierPath))

    return ModifierInvocation(
        modifier=name_parsed, args=arguments_parsed, **_extract_base_props(raw)
    )


def parse_event_definition(raw: Dict) -> EventDefinition:
    return EventDefinition(anonymous=raw["anonymous"], **_extract_call_props(raw))


def parse_elementary_type_name(raw: Dict) -> ElementaryTypeName:
    """
    name (string)
    """

    name = raw["name"]

    mutability = None
    if "stateMutability" in raw:
        mutability = raw["stateMutability"]

    return ElementaryTypeName(name=name, mutability=mutability, **_extract_base_props(raw))


def parse_user_defined_type_name(raw: Dict) -> UserDefinedTypeName:
    if "pathNode" in raw and raw["pathNode"]:
        identifier_path = parse(raw["pathNode"])
        # TODO does this need to be included in `UserDefinedTypeName`
        assert isinstance(identifier_path, IdentifierPath)
        name = identifier_path.name
    else:
        name = raw["name"]

    return UserDefinedTypeName(
        name=name,
        referenced_declaration=raw["referencedDeclaration"],
        type_str=raw["typeDescriptions"]["typeString"],
        **_extract_base_props(raw),
    )


def parse_function_type_name(raw: Dict) -> FunctionTypeName:
    params = parse(raw["parameterTypes"])
    assert isinstance(params, ParameterList)

    rets = parse(raw["returnParameterTypes"])
    assert isinstance(rets, ParameterList)

    if "stateMutability" in raw:
        # >=0.4.16
        mutability = raw["stateMutability"]
    elif "payable" in raw:
        # >=0.4.5
        mutability = "payable" if raw["payable"] else "nonpayable"
    else:
        raise ParsingError("don't know how to extract state mutability")

    return FunctionTypeName(
        params=params,
        rets=rets,
        mutability=mutability,
        visibility=raw["visibility"],
        **_extract_base_props(raw),
    )


def parse_mapping(raw: Dict) -> Mapping:
    key_parsed = parse(raw["keyType"])
    assert isinstance(key_parsed, TypeName)

    val_parsed = parse(raw["valueType"])
    assert isinstance(val_parsed, TypeName)

    return Mapping(key=key_parsed, value=val_parsed, **_extract_base_props(raw))


def parse_array_type_name(raw: Dict) -> ArrayTypeName:
    base_parsed = parse(raw["baseType"])
    assert isinstance(base_parsed, TypeName)

    len_parsed = None
    if "length" in raw and raw["length"]:
        len_parsed = parse(raw["length"])
        assert isinstance(len_parsed, Expression)

    return ArrayTypeName(base=base_parsed, len=len_parsed, **_extract_base_props(raw))


def parse_inline_assembly(raw: Dict) -> InlineAssembly:
    if "AST" in raw:
        # >= 0.6.0
        ast = raw["AST"]
        assert isinstance(ast, dict)
    elif "operations" in raw:
        # >= 0.4.12
        ast = raw["operations"]
        assert isinstance(ast, str)
    else:
        raise ParsingError("not sure now to extract inline assembly")
    return InlineAssembly(ast=ast, **_extract_base_props(raw))


def parse_unchecked_block(raw: Dict) -> UncheckedBlock:
    block = parse_block(raw)
    return UncheckedBlock(statements=block.statements, **_extract_base_props(raw))


def parse_block(raw: Dict) -> Block:
    """
    statements (Statement[]): list of statements
    """

    parsed_statements: List[Statement] = []
    for statement in raw["statements"]:
        parsed_statement = parse(statement)
        assert isinstance(parsed_statement, Statement)
        parsed_statements.append(parsed_statement)

    return Block(statements=parsed_statements, **_extract_base_props(raw))


def parse_placeholder_statement(raw: Dict) -> PlaceholderStatement:
    return PlaceholderStatement(**_extract_base_props(raw))


def parse_if_statement(raw: Dict) -> IfStatement:
    """
    condition (Expression)
    trueBody (Statement)
    falseBody (Statement)
    """

    condition_parsed = parse(raw["condition"])
    true_body_parsed = parse(raw["trueBody"])

    if "falseBody" in raw and raw["falseBody"]:
        false_body_parsed = parse(raw["falseBody"])
        assert isinstance(false_body_parsed, Statement)
    else:
        false_body_parsed = None

    assert isinstance(condition_parsed, Expression)
    assert isinstance(true_body_parsed, Statement)

    return IfStatement(
        condition=condition_parsed,
        true_body=true_body_parsed,
        false_body=false_body_parsed,
        **_extract_base_props(raw),
    )


def parse_try_catch_clause(raw: Dict) -> TryCatchClause:
    """
    errorName (string)
    parameters (ParameterList?)
    block (Block)
    """

    error_name = raw["errorName"]
    parameters_parsed = None
    if "parameters" in raw and raw["parameters"]:
        parameters_parsed = parse(raw["parameters"])
        assert isinstance(parameters_parsed, ParameterList)

    block_parsed = parse(raw["block"])
    assert isinstance(block_parsed, Block)

    return TryCatchClause(
        error_name=error_name,
        params=parameters_parsed,
        block=block_parsed,
        **_extract_base_props(raw),
    )


def parse_try_statement(raw: Dict) -> TryStatement:
    """
    externalCall (Expression)
    clauses (TryCatchClause[])
    """

    external_call_parsed = parse(raw["externalCall"])
    assert isinstance(external_call_parsed, Expression)

    clauses_parsed = []
    for child in raw["clauses"]:
        child_parsed = parse(child)
        assert isinstance(child_parsed, TryCatchClause)
        clauses_parsed.append(child_parsed)

    return TryStatement(
        external_call=external_call_parsed, clauses=clauses_parsed, **_extract_base_props(raw)
    )


def parse_while_statement_internal(raw: Dict, is_do_while: bool) -> WhileStatement:
    """
    condition (Expression)
    body (Statement)
    """

    condition_parsed = parse(raw["condition"])
    assert isinstance(condition_parsed, Expression)

    body_parsed = parse(raw["body"])
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
    """
    initializationExpression (Statement)
    condition (Expression)
    loopExpression (ExpressionStatement)
    body (Statement)
    """

    init_parsed = None
    if "initializationExpression" in raw and raw["initializationExpression"]:
        init_parsed = parse(raw["initializationExpression"])
        assert isinstance(init_parsed, Statement)

    cond_parsed = None
    if "condition" in raw and raw["condition"]:
        cond_parsed = parse(raw["condition"])
        assert isinstance(cond_parsed, Expression)

    loop_parsed = None
    if "loopExpression" in raw and raw["loopExpression"]:
        loop_parsed = parse(raw["loopExpression"])
        assert isinstance(loop_parsed, ExpressionStatement)

    body_parsed = parse(raw["body"])
    assert isinstance(body_parsed, Statement)

    return ForStatement(
        init=init_parsed,
        cond=cond_parsed,
        loop=loop_parsed,
        body=body_parsed,
        **_extract_base_props(raw),
    )


def parse_continue(raw: Dict) -> Continue:
    return Continue(**_extract_base_props(raw))


def parse_break(raw: Dict) -> Break:
    return Break(**_extract_base_props(raw))


def parse_return(raw: Dict) -> Return:
    """
    expression (Expression?)
    functionReturnParameters (int)
    """
    expr_parsed = None
    if "expression" in raw:
        expr_parsed = parse(raw["expression"])

    return Return(expression=expr_parsed, **_extract_base_props(raw))


def parse_revert_statement(raw: Dict) -> Revert:
    """
    errorCall (FunctionCall?)
    """
    error_call_parsed = None
    if "errorCall" in raw:
        error_call_parsed = parse(raw["errorCall"])
        assert isinstance(error_call_parsed, FunctionCall)

    return Revert(error_call=error_call_parsed, **_extract_base_props(raw))


def parse_throw(raw: Dict) -> Throw:
    return Throw(**_extract_base_props(raw))


def parse_emit_statement(raw: Dict) -> EmitStatement:
    """
    eventCall (FunctionCall)
    """
    call_parsed = parse(raw["eventCall"])
    assert isinstance(call_parsed, FunctionCall)

    return EmitStatement(event_call=call_parsed, **_extract_base_props(raw))


def parse_variable_declaration_statement(raw: Dict) -> VariableDeclarationStatement:
    """
    assignments (int[]): ids of variables declared
    declarations (VariableDeclaration[]): variables declared
    initialValue (Expression?): initial value, if any
    """

    parsed_variables: List[Optional[VariableDeclaration]] = []
    for declaration in raw["declarations"]:
        if declaration:
            parsed_variable = parse(declaration)
            assert isinstance(parsed_variable, VariableDeclaration)
            parsed_variables.append(parsed_variable)
        else:
            parsed_variables.append(None)  # TODO (success, )

    initial_value = None
    if "initialValue" in raw and raw["initialValue"]:
        initial_value = parse(raw["initialValue"])
        assert isinstance(initial_value, Expression)

    return VariableDeclarationStatement(
        variables=parsed_variables, initial_value=initial_value, **_extract_base_props(raw)
    )


def parse_expression_statement(raw: Dict) -> ExpressionStatement:
    """
    expression (Statement)
    """

    expression_parsed = parse(raw["expression"])

    assert isinstance(expression_parsed, Expression)

    return ExpressionStatement(expression=expression_parsed, **_extract_base_props(raw))


def parse_conditional(raw: Dict) -> Conditional:
    true_expr_parsed = parse(raw["trueExpression"])
    assert isinstance(true_expr_parsed, Expression)

    false_expr_parsed = parse(raw["falseExpression"])
    assert isinstance(false_expr_parsed, Expression)

    cond_parsed = parse(raw["condition"])
    assert isinstance(cond_parsed, Expression)

    return Conditional(
        condition=cond_parsed,
        true_expr=true_expr_parsed,
        false_expr=false_expr_parsed,
        **_extract_expr_props(raw),
    )


def parse_assignment(raw: Dict) -> Assignment:
    """
    operator (string)
    leftHandSide (Expression)
    rightHandSide (Expression)

    +Attributes
    """

    operator = raw["operator"]
    left_parsed = parse(raw["leftHandSide"])
    right_parsed = parse(raw["rightHandSide"])

    assert isinstance(operator, str)
    assert isinstance(left_parsed, Expression)
    assert isinstance(right_parsed, Expression)

    return Assignment(
        left=left_parsed, operator=operator, right=right_parsed, **_extract_expr_props(raw)
    )


def parse_tuple_expression(raw: Dict) -> TupleExpression:
    """
    isInlineArray (bool)
    components (Expression[])
    """

    is_array = raw["isInlineArray"]
    components_parsed = []
    for component in raw["components"]:
        if component:
            components_parsed.append(parse(component))
        else:
            components_parsed.append(None)

    return TupleExpression(
        components=components_parsed, is_array=is_array, **_extract_expr_props(raw)
    )


def parse_unary_operation(raw: Dict) -> UnaryOperation:
    """
    prefix (bool)
    operator (string)
    subExpression (Expression)
    """

    expression_parsed = parse(raw["subExpression"])
    assert isinstance(expression_parsed, Expression)

    return UnaryOperation(
        operator=raw["operator"],
        expression=expression_parsed,
        is_prefix=raw["prefix"],
        **_extract_expr_props(raw),
    )


def parse_binary_operation(raw: Dict) -> BinaryOperation:
    """
    leftExpression (Expression)
    operator (string)
    rightExpression (Expression)
    """

    left_parsed = parse(raw["leftExpression"])
    operator = raw["operator"]
    right_parsed = parse(raw["rightExpression"])

    assert isinstance(left_parsed, Expression)
    assert isinstance(operator, str)
    assert isinstance(right_parsed, Expression)

    return BinaryOperation(
        left=left_parsed, operator=operator, right=right_parsed, **_extract_expr_props(raw)
    )


def parse_function_call(raw: Dict) -> FunctionCall:
    """
    expression (Expression)
    names (string[])
    arguments (Expression[])
    tryCall (bool)
    kind (string)

    +Annotation
    """
    expression_parsed = parse(raw["expression"])
    assert isinstance(expression_parsed, Expression)

    names = raw["names"]
    arguments_parsed = []
    for child in raw["arguments"]:
        child_parsed = parse(child)
        assert isinstance(child_parsed, Expression)
        arguments_parsed.append(child_parsed)

    return FunctionCall(
        kind=raw["kind"],
        expression=expression_parsed,
        names=names,
        arguments=arguments_parsed,
        **_extract_expr_props(raw),
    )


def parse_function_call_options(raw: Dict) -> FunctionCallOptions:
    expression_parsed = parse(raw["expression"])
    assert isinstance(expression_parsed, Expression)

    names = raw["names"]
    assert isinstance(names, list)
    for name in names:
        assert isinstance(name, str)

    options_parsed: List[Expression] = []
    for child in raw["options"]:
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
    typename_parsed = parse(raw["typeName"])
    assert isinstance(typename_parsed, TypeName)

    return NewExpression(typename=typename_parsed, **_extract_expr_props(raw))


def parse_member_access(raw: Dict) -> MemberAccess:
    """
    memberName (string)
    expression (Expression)
    """

    expression_parsed = parse(raw["expression"])
    assert isinstance(expression_parsed, Expression)

    member_name = raw["memberName"]

    return MemberAccess(
        expression=expression_parsed, member_name=member_name, **_extract_expr_props(raw)
    )


def parse_index_access(raw: Dict) -> IndexAccess:
    base_parsed = parse(raw["baseExpression"])
    assert isinstance(base_parsed, Expression)

    index_parsed = None
    if "indexExpression" in raw and raw["indexExpression"]:
        index_parsed = parse(raw["indexExpression"])
        assert isinstance(index_parsed, Expression)

    return IndexAccess(base=base_parsed, index=index_parsed, **_extract_expr_props(raw))


def parse_index_range_access(raw: Dict) -> IndexRangeAccess:
    base_parsed = parse(raw["baseExpression"])
    assert isinstance(base_parsed, Expression)

    start_parsed = None
    if "startExpressionraw" in raw and raw["startExpression"]:
        parse(raw["startExpression"])
        assert isinstance(start_parsed, Expression)

    end_parsed = None
    if "endExpression" in raw and raw["endExpression"]:
        end_parsed = parse(raw["endExpression"])
        assert isinstance(end_parsed, Expression)

    return IndexRangeAccess(
        base=base_parsed, start=start_parsed, end=end_parsed, **_extract_expr_props(raw)
    )


def parse_identifier(raw: Dict) -> Identifier:
    """
    name (string)
    """

    name = raw["name"]
    assert isinstance(name, str)

    referenced_declaration = None
    if "referencedDeclaration" in raw:
        referenced_declaration = raw["referencedDeclaration"]
        assert isinstance(referenced_declaration, int)

    return Identifier(
        name=name, referenced_declaration=referenced_declaration, **_extract_expr_props(raw)
    )


def parse_elementary_type_name_expression(raw: Dict) -> ElementaryTypeNameExpression:
    if isinstance(raw["typeName"], dict):
        # >= 0.6.0
        typename_parsed = parse(raw["typeName"])
    else:
        # >= 0.4.12
        typename_parsed = ElementaryTypeName(
            name=raw["typeName"],
            mutability="default",
            **_extract_base_props(raw),
        )

    assert isinstance(typename_parsed, ElementaryTypeName)

    return ElementaryTypeNameExpression(typename=typename_parsed, **_extract_expr_props(raw))


def parse_literal(raw: Dict) -> Literal:
    """
    kind (string)
    value (string)
    hexValue (string)
    subdenomination (string?)

    +ExpressionAnnotation
    """
    subdenomination = raw.get("subdenomination", None)

    return Literal(
        kind=raw["kind"],
        value=raw["value"],
        hex_value=raw["hexValue"],
        subdenomination=subdenomination,
        **_extract_expr_props(raw),
    )


def parse_unsupported(raw: Dict) -> ASTNode:
    raise ParsingError("unsupported compact json node", raw["nodeType"], raw.keys(), raw)


def parse(raw: Dict) -> ASTNode:
    try:
        return PARSERS.get(raw["nodeType"], parse_unsupported)(raw)
    except ParsingError as e:
        raise e
    except Exception as e:
        raise ParsingError("failed to parse compact json node", raw["nodeType"], e, raw.keys(), raw)


PARSERS: Dict[str, Callable[[Dict], ASTNode]] = {
    "SourceUnit": parse_source_unit,
    "UserDefinedValueTypeDefinition": parse_user_defined_value_type_definition,
    "IdentifierPath": parse_identifier_path,
    "PragmaDirective": parse_pragma_directive,
    "ImportDirective": parse_import_directive,
    "ContractDefinition": parse_contract_definition,
    "InheritanceSpecifier": parse_inheritance_specifier,
    "UsingForDirective": parse_using_for_directive,
    "ErrorDefinition": parse_error_definition,
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
    "UncheckedBlock": parse_unchecked_block,
    "PlaceholderStatement": parse_placeholder_statement,
    "IfStatement": parse_if_statement,
    "TryCatchClause": parse_try_catch_clause,
    "TryStatement": parse_try_statement,
    "RevertStatement": parse_revert_statement,
    "WhileStatement": parse_while_statement,
    "DoWhileStatement": parse_do_while_statement,
    "ForStatement": parse_for_statement,
    "Continue": parse_continue,
    "Break": parse_break,
    "Return": parse_return,
    "Throw": parse_throw,
    "EmitStatement": parse_emit_statement,
    "VariableDeclarationStatement": parse_variable_declaration_statement,
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
    "Literal": parse_literal,
}
