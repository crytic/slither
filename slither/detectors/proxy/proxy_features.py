from abc import ABC

from inspect import currentframe, getframeinfo
from symtable import Function
from slither.detectors.abstract_detector import AbstractDetector, DetectorClassification
from typing import Optional, List, Dict, Set, Callable, Tuple, TYPE_CHECKING, Union
from slither.core.cfg.node import Node, NodeType
from slither.core.declarations.contract import Contract
from slither.core.compilation_unit import SlitherCompilationUnit
from slither.core.declarations.structure import Structure
from slither.core.declarations.structure_contract import StructureContract
from slither.core.declarations.solidity_variables import SolidityVariable, SolidityFunction
from slither.core.variables.variable import Variable
from slither.core.variables.state_variable import StateVariable
from slither.core.variables.local_variable import LocalVariable
from slither.core.variables.structure_variable import StructureVariable
from slither.core.expressions.identifier import Identifier
from slither.core.expressions.literal import Literal
from slither.core.declarations.function_contract import FunctionContract
from slither.core.expressions.expression import Expression
from slither.core.expressions.tuple_expression import TupleExpression
from slither.core.expressions.literal import Literal
from slither.core.expressions.call_expression import CallExpression
from slither.core.expressions.type_conversion import TypeConversion
from slither.core.expressions.assignment_operation import AssignmentOperation
from slither.core.expressions.conditional_expression import ConditionalExpression
from slither.core.expressions.binary_operation import BinaryOperation, BinaryOperationType
from slither.core.expressions.member_access import MemberAccess
from slither.core.expressions.index_access import IndexAccess
from slither.core.solidity_types.mapping_type import MappingType, Type
from slither.core.solidity_types.user_defined_type import UserDefinedType
from slither.core.solidity_types.elementary_type import ElementaryType
from slither.slithir.variables.temporary import TemporaryVariable
from slither.utils.function import get_function_id
import slither.analyses.data_dependency.data_dependency as data_dependency


class ProxyFeatureExtraction:
    """
    Wrapper class for extracting proxy features from a Contract object.
    Not a detector, but used exclusively by ProxyPatterns detector.
    """

    def __init__(self, contract: "Contract", compilation_unit: "SlitherCompilationUnit"):
        self.contract: Contract = contract
        self.compilation_unit: SlitherCompilationUnit = compilation_unit
        self._is_admin_only_proxy: Optional[bool] = None
        self._impl_address_variable: Optional["Variable"] = contract.delegate_variable
        self._impl_address_location: Optional["Contract"] = None
        self._proxy_only_contains_fallback: Optional[bool] = None
        self._has_time_delay: Optional[dict] = None

    ###################################################################################
    ###################################################################################
    # region general properties
    ###################################################################################
    ###################################################################################

    @property
    def is_proxy(self) -> bool:
        return self.contract.is_proxy

    @property
    def is_upgradeable_proxy(self) -> bool:
        return self.contract.is_upgradeable_proxy

    @property
    def is_upgradeable_proxy_confirmed(self) -> bool:
        return self.contract.is_upgradeable_proxy_confirmed

    @property
    def impl_address_variable(self) -> Optional["Variable"]:
        if self._impl_address_variable is None:
            self._impl_address_variable = self.contract.delegate_variable
        return self._impl_address_variable

    @property
    def impl_address_location(self) -> Optional["Contract"]:
        """
        Determine which contract the implementation address variable is declared in.

        :return: For state variables, just return the StateVariable.contract.
                 For local variables, return LocalVariable.function.contract
                  or self.contract if that contract is inherited by self.contract.
                 For structure variables, return StructureVariable.structure.contract.
        """
        if self._impl_address_location is None:
            if isinstance(self._impl_address_variable, StateVariable):
                self._impl_address_location = self._impl_address_variable.contract
            elif isinstance(self._impl_address_variable, LocalVariable):
                function = self._impl_address_variable.function
                if function is None:
                    self._impl_address_location = self.contract
                if isinstance(function, FunctionContract):
                    self._impl_address_location = function.contract
                    if self._impl_address_location in self.contract.inheritance:
                        self._impl_address_location = self.contract
            elif isinstance(self._impl_address_variable, StructureVariable):
                struct = self._impl_address_variable.structure
                if isinstance(struct, StructureContract):
                    self._impl_address_location = struct.contract
            # dependencies = data_dependency.get_dependencies_recursive(self._impl_address_variable,
            #                                                           self._impl_address_location)
        return self._impl_address_location

    def is_impl_address_also_declared_in_logic(self) -> (int, Optional[Contract]):
        """
        If the implementation address variable is a StateVariable declared in the proxy,
        but the implementation setter is not declared in the proxy, then we need to determine
        if the implementation contract declares the same variable in the same slot.

        :return: The index indicating the position of the variable declaration, i.e. slot 0,
                 and the Contract in which the variable (and its setter) is also declared,
                 or else return -1 and None if this is not the case.
        """
        ret_index = -1
        ret_contract = None
        if isinstance(self._impl_address_variable, StateVariable):
            delegate = self._impl_address_variable
            setter = self.contract.proxy_implementation_setter
            if setter is not None and setter.contract != self.contract:
                ret_contract = setter.contract
                index = -1
                for idx, var in enumerate(self.contract.state_variables_ordered):
                    if var == delegate:
                        index = idx
                        break
                if index >= 0 and len(ret_contract.state_variables_ordered) >= index + 1:
                    var = ret_contract.state_variables_ordered[index]
                    if var is not None:
                        if var.name == delegate.name and var.type == delegate.type:
                            ret_index = index
        return ret_index, ret_contract

    def find_slot_in_setter_asm(self) -> Optional[str]:
        slot = None
        setter = self.contract.proxy_implementation_setter
        if setter is not None:
            for node in setter.all_nodes():
                if node.type == NodeType.ASSEMBLY and node.inline_asm is not None:
                    inline_asm = node.inline_asm
                    if "AST" in inline_asm and isinstance(inline_asm, Dict):
                        for statement in inline_asm["AST"]["statements"]:
                            if statement["nodeType"] == "YulExpressionStatement":
                                statement = statement["expression"]
                            if statement["nodeType"] == "YulVariableDeclaration":
                                statement = statement["value"]
                            if statement["nodeType"] == "YulFunctionCall":
                                if statement["functionName"]["name"] == "sstore":
                                    slot = statement["arguments"][0]
                    else:
                        asm_split = inline_asm.split("\n")
                        for asm in asm_split:
                            if "sstore" in asm:
                                params = asm.split("(")[1].strip(")").split(", ")
                                slot = params[0]
                    if slot is not None:
                        sv = self.contract.get_state_variable_from_name(slot)
                        if sv is None:
                            lv = node.function.get_local_variable_from_name(slot)
                            if lv is not None and lv.expression is not None and isinstance(lv.expression,
                                                                                           Identifier):
                                if isinstance(lv.expression.value, StateVariable):
                                    sv = lv.expression.value
                        if sv is not None and sv.expression is not None:
                            slot = str(sv.expression)
                        break
        return slot

    def all_mappings(self) -> Optional[List["MappingType"]]:
        """
        :return: List of all MappingType state variables found in the contract, or None if empty
        """
        mappings = []
        for v in self.contract.state_variables:
            if isinstance(v.type, MappingType):
                mappings.append(v.type)
        if len(mappings) == 0:
            return None
        return mappings

    def is_eternal_storage(self) -> bool:
        """
        Contracts using Eternal Storage must contain the following mappings:
            mapping(bytes32 => uint256) internal uintStorage;
            mapping(bytes32 => string) internal stringStorage;
            mapping(bytes32 => address) internal addressStorage;
            mapping(bytes32 => bytes) internal bytesStorage;
            mapping(bytes32 => bool) internal boolStorage;
            mapping(bytes32 => int256) internal intStorage;
        Note: the implementation address variable may be stored separately.

        :return: True if all of the above mappings are present, otherwise False.
        """
        mappings = self.all_mappings()
        types = ["uint256", "string", "address", "bytes", "bool", "int256"]
        if mappings is not None:
            maps_to = [str(m.type_to) for m in mappings]
            return all([t in maps_to for t in types])
        return False

    def find_impl_slot_from_sload(self) -> str:
        """
        Given the implementation address variable (which should be a LocalVariable
        if loaded from a storage slot), searches the CFG of the fallback function
        to extract the value of the storage slot it is loaded from (using sload).

        :return: A string, which should be the 32-byte storage slot location.
        """
        fallback = self.contract.fallback_function
        delegate = self.contract.delegate_variable
        if delegate == self.contract.proxy_impl_storage_offset:
            return str(delegate.expression)
        slot = None
        """
        Use slither.analysis.data_dependency to expedite analysis if possible.
        """
        for sv in self.contract.state_variables:
            if data_dependency.is_dependent(delegate, sv, self.contract):
                # print(f"{delegate} is dependent on {sv}")
                if str(sv.type) == "bytes32" and sv.is_constant:
                    getter = self.contract.proxy_implementation_getter
                    if getter is not None and getter.contains_assembly and getter.is_reading(sv):
                        asm_nodes = [node for node in getter.all_nodes()
                                     if node.type == NodeType.ASSEMBLY and node.inline_asm is not None]
                        for node in asm_nodes:
                            if "sload" in node.inline_asm:
                                return str(sv.expression)
        """
        Check if the slot was found during the initial execution of Contract.is_upgradeable_proxy().
        Comment out to ensure the rest of the code here works without it.
        """
        slot = self.contract.proxy_impl_storage_offset
        if slot is not None:
            if len(slot.name) == 66 and slot.name.startswith("0x"):
                return slot.name
            else:
                return str(slot.expression)
        if delegate.expression is not None:
            """
            Means the variable was assigned a value when it was first declared. 
            """
            exp = delegate.expression
            # print(f"Expression for {delegate}: {exp}")
            if isinstance(exp, Identifier):
                v = self.unwrap_identifiers(self.impl_address_location, exp)
                if v.expression is not None:
                    exp = v.expression
                # else:
                    # print(f"{v}.expression is None")
            if isinstance(exp, MemberAccess):
                # print(f"MemberAccess: {exp.expression}")
                exp = exp.expression
            if isinstance(exp, CallExpression):
                # print(f"Called: {exp.called}")
                # if str(exp.called).startswith("sload"):
                if len(exp.arguments) > 0:
                    arg = exp.arguments[0]
                    if len(str(arg)) == 66 and str(arg).startswith("0x"):
                        return str(arg)
                    elif isinstance(arg, Identifier):
                        v = self.unwrap_identifiers(self.impl_address_location, arg)
                        if v.expression is not None:
                            exp = v.expression
                            if v.is_constant:
                                return str(v.expression)
                            elif str(v.type) == "bytes32":
                                return str(v)
                            elif isinstance(exp, Literal):
                                return str(exp)
                        # else:
                        #     print(f"{v}.expression is None")
                    # else:
                    #     print(f"CallExpression argument {arg} is not an Identifier")
        else:
            """
            Means the variable was declared before it was assigned a value.
            i.e., if the return value was given a name in the function signature.
            In this case we must search for where it was assigned a value. 
            """
            # print(f"Expression for {delegate} is None")
            func = self.contract.proxy_implementation_getter
            if func is None:
                func = fallback
            for node in func.all_nodes():
                if node.type == NodeType.VARIABLE:
                    if node.variable_declaration != delegate:
                        continue
                    exp = node.variable_declaration.expression
                    # print(f"find_impl_slot_from_sload: VARIABLE node: {exp}")
                    if exp is not None and isinstance(exp, Identifier):
                        slot = str(exp.value.expression)
                        return slot
                elif node.type == NodeType.EXPRESSION:
                    exp = node.expression
                    # print(f"find_impl_slot_from_sload: EXPRESSION node: {exp}")
                    if isinstance(exp, AssignmentOperation):
                        left = exp.expression_left
                        right = exp.expression_right
                        if isinstance(left, Identifier) and left.value == delegate:
                            if isinstance(right, CallExpression) and str(right.called) == "sload":
                                slot = right.arguments[0]
                elif node.type == NodeType.ASSEMBLY:
                    # print(f"find_impl_slot_from_sload: ASSEMBLY node: {node.inline_asm}")
                    if "AST" in node.inline_asm and isinstance(node.inline_asm, Dict):
                        for statement in node.inline_asm["AST"]["statements"]:
                            if statement["nodeType"] == "YulExpressionStatement":
                                statement = statement["expression"]
                            if statement["nodeType"] == "YulVariableDeclaration":
                                if statement["variables"][0]["name"] != delegate.name:
                                    continue
                                statement = statement["value"]
                            if statement["nodeType"] == "YulAssignment":
                                if statement["variableNames"][0]["name"] != delegate.name:
                                    continue
                                statement = statement["value"]
                            if statement["nodeType"] == "YulFunctionCall":
                                if statement["functionName"]["name"] == "sload":
                                    slot = statement["arguments"][0]["name"]
                    else:
                        asm_split = node.inline_asm.split("\n")
                        for asm in asm_split:
                            # print(f"checking assembly line: {asm}")
                            if "sload" in asm and str(delegate) in asm:
                                slot = asm.split("(")[1].strip(")")
                if slot is not None and len(str(slot)) != 66:
                    sv = self.contract.get_state_variable_from_name(slot)
                    if sv is None:
                        lv = node.function.get_local_variable_from_name(slot)
                        if lv is not None and lv.expression is not None:
                            exp = lv.expression
                            while isinstance(exp, Identifier) and isinstance(exp.value, LocalVariable):
                                exp = exp.value.expression
                            if isinstance(exp, Identifier) and isinstance(exp.value, StateVariable):
                                sv = exp.value
                    if sv is not None and sv.expression is not None and (sv.is_constant or str(sv.type) == "bytes32"):
                        slot = str(sv.expression)
                        break
                    # elif sv is not None and sv.expression is None:
                    #     print(f"{sv} is missing an expression")
                    # else:
                    #     print(f"Could not find StateVariable from {slot}")
                elif slot is not None:
                    break
        return slot

    def proxy_only_contains_fallback(self) -> bool:
        """
        Determine whether the proxy contract contains any external/public functions
        besides the fallback, not including the constructor or receive function.

        :return: False if any other external/public function is found, or if the
                 fallback function is missing, otherwise True
        """
        if self._proxy_only_contains_fallback is None:
            self._proxy_only_contains_fallback = False
            for function in self.contract.functions:
                if function.is_fallback:
                    # print(f"Found {function.name}")
                    self._proxy_only_contains_fallback = True
                elif function.visibility in ["external", "public"]:
                    # print(f"Found {function.visibility} function: {function.name}")
                    if function.is_receive or function.is_constructor:
                        continue
                    self._proxy_only_contains_fallback = False
                    return self._proxy_only_contains_fallback
        return self._proxy_only_contains_fallback

    def has_transparent_admin_checks(self) -> (bool, str):
        """
        Determine whether all external functions (besides fallback() and receive())
        are only callable by a specific address, and whether the fallback and receive
        functions are only callable by addresses other than the same specific address,
        i.e., whether this proxy uses the Transparent Proxy pattern.

        :return: True if the above conditions are met, otherwise False
        """
        admin_str = None
        checks = []
        has_external_functions = False
        for function in self.contract.functions:
            if not function.is_fallback and not function.is_constructor and not function.is_receive:
                """
                Check for 'msg.sender ==' comparison in all external/public functions 
                besides fallback, receive and constructor
                """
                comparator = "=="
            elif not function.is_constructor:
                """
                Check for 'msg.sender !=' comparison in fallback and receive functions
                """
                comparator = "!="
            else:
                """
                Skip the constructor
                """
                continue
            if function.visibility in ["external", "public"]:
                has_external_functions = True
                if not function.is_protected():
                    return False, None
                check, admin_str = self.is_function_protected_with_comparator(function, comparator, admin_str)
                checks.append(check)
        return (all(checks) and has_external_functions), admin_str

    def impl_address_from_contract_call(self) -> (bool, Optional[Expression], Optional[Type]):
        """
        Determine whether the proxy contract retrieves the address of the
        implementation contract by calling a function in a third contract,
        i.e. from a Beacon or Registry contract.

        Note: Because the initial execution of contract.is_upgradeable_proxy()
              performs cross-contract analysis to trace this contract call,
              if successful, impl_address_variable will be a StateVariable
              declared in said third contract. But what we really want is a
              LocalVariable which gets its value from a CallExpression, which
              is what we'd have if the initial cross-contract analysis failed.

        :return: True if cross-contract call was found, as well as the actual
                 CallExpression and the Type of the contract being called.
                 Otherwise, returns (False, None, None).
        """
        delegate = self.impl_address_variable
        e = delegate.expression
        # print(f"impl_address_from_contract_call: {e}")
        ret_exp = None
        c_type = None
        is_cross_contract = False
        if isinstance(delegate, StateVariable) and delegate.contract != self.contract:
            # print(f"impl_address_from_contract_call: StateVariable {delegate}")
            """
            This indicates that cross-contract analysis during the initial execution of
            contract.is_upgradeable_proxy() was able to identify the variable which is
            returned by the cross-contract call. In this case, in order to return the
            CallExpression which returned this value, we need to re-find it first.
            """
            getter = self.contract.proxy_implementation_getter
            # print(f"impl_address_from_contract_call: getter is {getter}")
            if getter is None and delegate.visibility in ["public", "external"]:
                getter = delegate
            elif getter is not None:
                # print(f"getter.full_name = {getter.full_name}")

                for call in self.contract.all_library_calls:
                    print(str(call))

                for call in self.contract.all_library_calls:
                    # print(f"library call: {c.name}.{f.name}")
                    if call.function and isinstance(call.function, Function):
                        function_name = call.function.canonical_name
                        if function_name == getter.canonical_name:
                            # print(f"Found {getter} in {self.contract.name}.all_library_calls")
                            return is_cross_contract, ret_exp, c_type
            for node in self.contract.fallback_function.all_nodes():
                exp = node.expression
                if isinstance(exp, AssignmentOperation):
                    exp = exp.expression_right
                    """Fall through to below"""
                if isinstance(exp, CallExpression):
                    # print(f"impl_address_from_contract_call: CallExpression {exp}")
                    called = exp.called
                    if isinstance(called, Identifier):
                        f = called.value
                        if isinstance(f, FunctionContract) and f == getter \
                                and f.contract != self.contract and f.contract not in self.contract.inheritance:
                            e = exp
                            # print(f"found CallExpression calling getter in another contract: {e}")
                            break
                        elif len(exp.arguments) > 0:
                            for arg in exp.arguments:
                                # print(f"impl_address_from_contract_call: arg is {arg}")
                                if isinstance(arg, CallExpression):
                                    # print(f"impl_address_from_contract_call: CallExpression {arg}")
                                    exp = arg
                                    called = arg.called
                                    break
                    if isinstance(called, MemberAccess) and called.member_name == getter.name:
                        e = exp
                        # print(f"found MemberAccess calling getter in another contract: {e}")
                        break
        while isinstance(e, CallExpression):
            """
            Unwrap the (possibly nested) function calls until a MemberAccess is found.
            An example of why this is necessary (from tests/proxies/APMRegistry.sol):
                function () payable public {
                    address target = getCode();
                    require(target != 0); // if app code hasn't been set yet, don't call
                    delegatedFwd(target, msg.data);
                }
                function getCode() public view returns (address) {
                    return getAppBase(appId);
                }
                function getAppBase(bytes32 _appId) internal view returns (address) {
                    return kernel.getApp(keccak256(APP_BASES_NAMESPACE, _appId));
                }
            """
            called = e.called
            # print(f"called: {called}")
            if isinstance(called, Identifier):
                f = called.value
                if isinstance(f, FunctionContract) and f.return_node() is not None:
                    e = f.return_node().expression
                    # print(f"{called} returns {e}")

                elif isinstance(f, SolidityFunction):
                    break
                else:
                    e = f.expression
            elif isinstance(called, MemberAccess):
                ret_exp = e
                e = called
                # print(f"found MemberAccess: {e}")
            else:
                # print(f"{called} is not Identifier or MemberAccess")
                break
        if isinstance(e, MemberAccess):
            e = e.expression
            if isinstance(e, CallExpression) and isinstance(e.called, Identifier):
                f = e.called.value
                if isinstance(f, FunctionContract):
                    ret_node = f.return_node()
                    if ret_node is not None:
                        e = f.return_node().expression
                    else:
                        ret_val = f.returns[0]
                        e = Identifier(ret_val)
            if isinstance(e, TypeConversion) or isinstance(e, Identifier):
                c_type = e.type
                if isinstance(e, Identifier):
                    # print(f"Identifier: {e}")
                    if isinstance(e.value, Contract):
                        # print(f"value is Contract: {e.value}")
                        c_type = UserDefinedType(e.value)
                    else:
                        c_type = e.value.type
                        # if isinstance(e.value, StateVariable):
                        #     print(f"value is StateVariable: {e.value}\nType: {c_type}")
                elif isinstance(e, TypeConversion):
                    # print(f"TypeConversion: {e}")
                    exp = e.expression
                    if isinstance(exp, Literal) and not isinstance(ret_exp, CallExpression):
                        ret_exp = exp
                if isinstance(c_type, UserDefinedType) and isinstance(c_type.type,
                                                                      Contract) and c_type.type != self:
                    is_cross_contract = True
                    if c_type.type.is_interface or (getter is not None and c_type.type != getter.contract):
                        for c in self.compilation_unit.contracts:
                            if c_type.type in c.inheritance:
                                c_type = UserDefinedType(c)
                elif str(c_type) == "address":
                    is_cross_contract = True
                    getter = self.contract.proxy_implementation_getter
                    if getter is not None and getter.contract != self.contract:
                        c_type = UserDefinedType(getter.contract)
        return is_cross_contract, ret_exp, c_type

    def find_registry_address_source(self, call: CallExpression) -> Optional[Variable]:
        """
        Determine the source of the address of the third contract from which the proxy retrieves
        its implementation address, i.e., where the Registry/Beacon address is stored.

        :param call: The CallExpression returned by impl_address_from_contract_call()
        """
        # print(f"find_registry_address_source: {call}")
        exp = call.called
        value = None
        if isinstance(exp, MemberAccess):
            # print(f"MemberAccess: {exp}")
            exp = exp.expression
            """fall-through to below"""
        if isinstance(exp, TypeConversion):
            # print(f"TypeConversion: {exp}")
            exp = exp.expression
            """fall-through to below"""
        if isinstance(exp, CallExpression):
            # print(f"CallExpression: {exp}")
            exp = exp.called
            """fall-through to below"""
        if isinstance(exp, Identifier):
            # print(f"Identifier: {exp}")
            value = exp.value
            if isinstance(value, LocalVariable):
                func = value.function
                if isinstance(func, FunctionContract):
                    dependencies = data_dependency.get_dependencies_recursive(value, func.contract)
                    # print(f"dependencies for {value} in context {func.contract}: "
                    #       f"{[str(dep) for dep in dependencies]}")
                    for dep in dependencies:
                        if isinstance(dep, TemporaryVariable):
                            dep_exp = dep.expression
                            # print(f"TemporaryVariable expression: {dep_exp}")
                            if isinstance(dep_exp, CallExpression) and isinstance(dep_exp.called, Identifier):
                                value = dep_exp.called.value
                        elif isinstance(dep, StateVariable) and str(dep.type) == "bytes32":
                            value = dep
                            break
            if isinstance(value, FunctionContract):
                func = value
                if len(func.returns) > 0:
                    value = func.returns[0]
                    ret_node = func.return_node()
                    if ret_node is not None and (value.name is None or value.name == ""):
                        """
                        If return value is unnamed, check return node expression
                        """
                        exp = ret_node.expression
                        if exp is not None:
                            if isinstance(exp, CallExpression):
                                """recursive call with new expression"""
                                return self.find_registry_address_source(exp)
                            if isinstance(exp, Identifier):
                                value = exp.value
                    elif value.name is not None and value.name != "":
                        """
                        If return value is named, find where it is assigned a value
                        """
                        for node in func.all_nodes():
                            if node.type == NodeType.EXPRESSION:
                                exp = node.expression
                                # print(f"EXPRESSION node: {exp}")
                                if isinstance(exp, AssignmentOperation):
                                    left = exp.expression_left
                                    right = exp.expression_right
                                    if isinstance(left, Identifier) and left.value == value:
                                        if isinstance(right, CallExpression):
                                            # print(f"Called: {right.called}")
                                            if str(right.called).startswith("sload"):
                                                exp = right.arguments[0]
                                                if isinstance(exp, Identifier):
                                                    value = exp.value
                                                if isinstance(value, LocalVariable):
                                                    exp = value.expression
                                                    if isinstance(exp, Identifier):
                                                        value = exp.value
                                            else:
                                                return self.find_registry_address_source(right)
                                        if isinstance(right, Identifier):
                                            value = right.value
                                            break
                            elif node.type == NodeType.ASSEMBLY:
                                if "AST" not in node.inline_asm and not isinstance(node.inline_asm, Dict):
                                    asm_split = node.inline_asm.split("\n")
                                    for asm in asm_split:
                                        # print(f"checking assembly line: {asm}")
                                        if "sload" in asm and value.name in asm:
                                            slot = asm.split("(")[1].strip(")")
                                            value = self.contract.get_state_variable_from_name(slot)
                                            if value is None:
                                                lv = node.function.get_local_variable_from_name(slot)
                                                if lv is not None and lv.expression is not None:
                                                    exp = lv.expression
                                                    if isinstance(exp, Identifier) and isinstance(exp.value,
                                                                                                  StateVariable):
                                                        value = exp.value
        return value

    def is_mapping_from_msg_sig(self, mapping: Variable) -> bool:
        """
        Determine whether the given variable is a mapping with function signatures as keys

        :param mapping: Should be a Variable with mapping.type == MappingType
        :return: True if a matching IndexAccess expression is found using msg.sig as the key, otherwise False
        """
        ret = False
        m_type = mapping.type
        if isinstance(m_type, MappingType):
            if str(m_type.type_from) != "bytes4":
                return False
            for node in self.contract.fallback_function.all_nodes():
                if node.type == NodeType.EXPRESSION or node.type == NodeType.VARIABLE:
                    if node.expression is None:
                        continue
                    exp = node.expression
                    if isinstance(exp, AssignmentOperation):
                        exp = exp.expression_right
                    while isinstance(exp, TypeConversion):
                        exp = exp.expression
                    if isinstance(exp, MemberAccess):
                        exp = exp.expression
                    if isinstance(exp, IndexAccess):
                        if mapping.name in str(exp.expression_left) and str(exp.expression_right) == "msg.sig":
                            ret = True
        return ret

    def has_compatibility_checks(self) -> (bool, List[Tuple[FunctionContract, Optional[Expression], bool]]):
        """
        For every function that can update the implementation address,
        determines whether it contains a compatibility check expression.

        Examples of compatibility checks:
        for ERC-1967, require that the new implementation is a contract:
            require(OpenZeppelinUpgradesAddress.isContract(newImplementation),
                           "Cannot set a proxy implementation to a non-contract address");
        for EIP-1822 (UUPS), require the new implementation uses the correct slot:
            require(bytes32(0xc5f16f0fcc639fa48a6947836d9850f504798523bf8c9a3a87d5876cf622bcf7)
                           == Proxiable(newAddress).proxiableUUID(), "Not compatible");

        :return: True if all update functions have checks,
                 plus a list of each Function and check Expression
        """
        all_checks = []
        func_exp_list: List[Tuple[FunctionContract, Optional[Expression], bool]] = []
        delegate = self.impl_address_variable
        writing_funcs = self.functions_writing_to_delegate(delegate, self.contract)
        setter = self.contract.proxy_implementation_setter
        getter = self.contract.proxy_implementation_getter
        dependencies = list(data_dependency.get_dependencies_recursive(delegate, self.contract))
        if setter is not None and setter.contract != self.contract:
            dependencies += list(data_dependency.get_dependencies_recursive(delegate, setter.contract))
        elif getter is not None and getter.contract != self.contract:
            dependencies += list(data_dependency.get_dependencies_recursive(delegate, getter.contract))
        dependencies = set(dependencies)
        # print(f"has_compatibility_checks: dependencies: {[str(dep) for dep in dependencies]}")
        for dep in dependencies:
            if isinstance(dep, StateVariable):
                writing_funcs += self.functions_writing_to_delegate(dep, dep.contract)
        for (func, var_written) in writing_funcs:
            if isinstance(func, FunctionContract):
                if func.visibility in ["internal", "private"] and func != setter:
                    # print(f"has_compatibility_checks: skipping {func.visibility} function {func}")
                    continue
                # else:
                #     print(f"has_compatibility_checks: checking {func.visibility} function {func}")
                check_exp = None
                has_check = False
                for node in func.all_nodes():
                    exp = node.expression
                    """
                    Search each upgrade function's expressions for a condition that will 
                    revert if the new implementation is not compatible with the proxy.
                    """
                    if isinstance(exp, CallExpression):
                        called = exp.called
                        if isinstance(called, Identifier):
                            """
                            For some early versions of Solidity, like 0.4.21, Slither wraps
                            SolidityFunctions in an Identifier when found in a CallExpression.
                            i.e., exp.called.value is the SolidityFunction object.
                            For later versions, exp.called is the SolidityFunction.
                            """
                            called = called.value
                        if isinstance(called, SolidityFunction):
                            """
                            Only CallExpressions we care about here are require and assert
                            """
                            if called.name in ["require(bool)", "require(bool,string)", "assert(bool)"]:
                                # print(exp)
                                condition = exp.arguments[0]
                                # print(f"has_compatibility_checks: condition {condition}")
                                """
                                The static helper method check_condition_from_expression will return an
                                Expression object if exp is a compatibility check, and will append any
                                newly found checks to the list of (function, compatibility check) pairs.
                                """
                                check_, func_exp_list = self.check_condition_from_expression(
                                    condition, func, var_written, func_exp_list, exp
                                )
                                """
                                Since there may be more than one valid compatibility check in the same function,
                                it is possible for the call above to return a check expression the first time,
                                setting has_check = True, and then return None after checking another expression
                                in the same function. Therefore, we do not want to overwrite check_exp above 
                                if the subsequent call to check_condition_from_expression returned None.
                                """
                                if check_ is not None:
                                    check_exp = check_
                                    has_check = True
                    # elif isinstance(exp, ConditionalExpression):
                    #     """
                    #     Even when there is clearly an if-else block in the source code, Function.all_expressions()
                    #     never seems to contain any ConditionalExpression objects. Rather, only the condition itself,
                    #     often a BinaryOperation or an Identifier for a boolean variable, and the expressions within
                    #     the `then` and `else` blocks appear in the list of all expressions. Therefore we need to use
                    #     Function.all_nodes() instead to find the IF nodes in the CFG. Unfortunately we cannot use
                    #     all_nodes() instead of all_expressions() for the section above, because all_nodes() does not
                    #     handle Solidity function CallExpressions correctly.
                    #     """
                    #     print(f"has_compatibility_checks: ConditionalExpression {exp}")
                    elif isinstance(exp, AssignmentOperation):
                        """
                        Need to check for incorrect compatibility check where the variable written is a Contract type,
                        as in the following example from PurgeableSynth.sol:
                            function setTarget(Proxyable _target)
                                external
                                onlyOwner
                            {
                                target = _target;
                                emit TargetUpdated(_target);
                            }
                        After compilation and deployment, the EVM converts the function's ABI to `setTarget(address)` and
                        does not perform any type checking to ensure the address given is actually a Proxyable contract,
                        even though the function signature in Solidity gives the impression that it would check the type.
                        """
                        left = exp.expression_left
                        right = exp.expression_right
                        if isinstance(left, Identifier) and isinstance(right, Identifier) \
                                and left.value == delegate and right.value == var_written:
                            if isinstance(var_written, LocalVariable) and isinstance(func, FunctionContract):
                                var_type = var_written.type
                                if isinstance(var_type, UserDefinedType):
                                    # print(f"has_compatibility_checks: {var_written}"
                                    #       f" is UserDefinedType: {var_type}")
                                    var_type = var_type.type
                                if isinstance(var_type, Contract):
                                    # print(f"has_compatibility_checks: {var_written}"
                                    #       f" is Contract type: {var_type}")
                                    if var_written in func.parameters:
                                        check_exp = exp
                                        has_check = True
                                        is_check_correct = False
                                        func_exp_list.append((func, check_exp, is_check_correct))
                    elif node.type == NodeType.IF:
                        # print(f"has_compatibility_checks: IF node exp = {exp}")
                        """
                        Found an IF node, so check if it can lead to a revert.
                        Node.sons only gives us the immediate children of the IF node,
                        i.e., the first node in the `then` block and the `else` block.
                        """
                        # TODO: It may be better to implement a recursive getter for Node children.
                        # TODO: Use Dominators / Control Dependency Graph instead
                        if any(["revert(" in str(son.expression) for son in node.sons if son.expression is not None]):
                            # print("has_compatibility_checks: IF node can lead to revert"
                            #       f" {[str(son.expression) for son in node.sons if son.expression is not None]}")
                            """
                            Unfortunately the IF Node does not contain a ConditionalExpression
                            already, so we must construct one using the CFG info from the Node. 
                            """
                            if len(node.sons) > 1:
                                # print("has_compatibility_checks: IF node can lead to revert"
                                #       f" {[str(son.expression) for son in node.sons if son.expression is not None]}")
                                son0 = node.sons[0]
                                while son0.expression is None and son0.sons[0] is not None:
                                    son0 = son0.sons[0]
                                son1 = node.sons[1]
                                while son1.expression is None and son1.sons[0] is not None:
                                    son1 = son1.sons[0]
                                conditional_exp = ConditionalExpression(exp, son0.expression, son1.expression)
                            else:
                                conditional_exp = ConditionalExpression(exp, node.sons[0].expression)
                            # print(f"has_compatibility_checks: ConditionalExpression {conditional_exp}")
                            """
                            The static helper method check_condition_from_expression will return an
                            Expression object if exp is a compatibility check, and will append any
                            newly found checks to the list of (function, compatibility check) pairs.
                            """
                            check_, func_exp_list = self.check_condition_from_expression(
                                exp, func, var_written, func_exp_list, conditional_exp
                            )
                            """
                            Since there may be more than one valid compatibility check in the same function,
                            it is possible for the call above to return a check expression the first time,
                            setting has_check = True, and then return None after checking another expression
                            in the same function. Therefore, we do not want to overwrite check_exp above 
                            if the subsequent call to check_condition_from_expression returned None.
                            """
                            if check_ is not None:
                                check_exp = check_
                                has_check = True
                if check_exp is None:
                    """ Didn't find check in this function """
                    func_exp_list.append((func, None, False))
            all_checks.append(has_check)
        return all(all_checks), func_exp_list

    def functions_writing_to_delegate(
            self,
            delegate: Variable,
            contract: Contract
    ) -> List[Tuple[FunctionContract, LocalVariable]]:
        """
        Contract.get_functions_writing_to_variable doesn't always work for us,
        for instance when a function writes to a storage slot in assembly.
        So this helper method finds all functions writing to the delegate variable.

        :param delegate: The Variable we are interested in
        :param contract: The Contract in which to search
        :return: List of FunctionContract objects and the values they write to delegate
        """
        setters = []
        setter = self.contract.proxy_implementation_setter
        slot = self.contract.proxy_impl_storage_offset
        to_search = contract.functions
        # print(f"functions_writing_to_variable: {delegate}")
        if setter is not None and setter.contract != contract:
            """
            If the implementation setter was found in a different contract, 
            then we must also search all of the functions in that contract.
            """
            to_search += setter.contract.functions
        for func in set(to_search):
            if isinstance(delegate, LocalVariable) and delegate.function == func:
                """
                If the implementation address variable extracted during the initial analysis
                is a LocalVariable, then the function in which it was declared is likely the 
                implementation getter, which we are not interested in.
                """
                continue
            value_written = None
            # print(f"functions_writing_to_variable: checking function {func.contract.name}.{func}"
            #       f" (proxy_features line:{getframeinfo(currentframe()).lineno})")
            if func.is_writing(delegate) and delegate not in func.returns:
                """
                Function.is_writing only works in the simplest cases, i.e., when writing to
                a typical StateVariable or LocalVariable. This does not work for patterns
                like Unstructured Storage or Diamond Storage.
                We still need to search the Expressions in func.expressions in order to 
                find the AssignmentOperation and extract the value being written.
                """
                for exp in func.expressions:
                    # print(f"functions_writing_to_variable: exp = {exp}"
                    #       f" (proxy_features line:{getframeinfo(currentframe()).lineno})")
                    if isinstance(exp, AssignmentOperation):
                        # print(f"functions_writing_to_variable: AssignmentOperation: {exp}"
                        #       f" (proxy_features line:{getframeinfo(currentframe()).lineno})")
                        left = exp.expression_left
                        right = exp.expression_right
                        if isinstance(left, IndexAccess):
                            """
                            If the delegate variable is a mapping, then we expect an IndexAccess
                            """
                            # print(f"functions_writing_to_variable: IndexAccess: {left}"
                            #       f" (proxy_features line:{getframeinfo(currentframe()).lineno})")
                            left = left.expression_left
                        if isinstance(left, Identifier) and left.value == delegate:
                            # print(f"functions_writing_to_variable: Identifier: {left}"
                            #       f" (proxy_features line:{getframeinfo(currentframe()).lineno})")
                            value_written = self.get_value_assigned(exp)
                if value_written is not None:
                    setters.append([func, value_written])
                    # print(f"functions_writing_to_variable: {func} writes {value_written} to {delegate}"
                    #       f" (proxy_features line:{getframeinfo(currentframe()).lineno})")
            elif slot is not None:
                """
                If the implementation address storage slot was detected during the initial analysis,
                then we need to search the CFG to find where the slot is used to store a new value.
                """
                for node in func.all_nodes():
                    if node.type == NodeType.ASSEMBLY:
                        """
                        Only search an ASSEMBLY Node if the Solidity version is < 0.6.0, because
                        in that case the assembly code is not also captured in EXPRESSION Nodes.
                        We can tell if it is < 0.6.0 if node.inline_asm is a string, not a Dict. 
                        """
                        if isinstance(node.inline_asm, str) and "sstore" in node.inline_asm:
                            asm_split = node.inline_asm.split("\n")
                            """
                            Only bother extracting the sstore if the function is actually using
                            the implementation slot. Without the line below, this would return any
                            function that uses sstore, even if it is using the admin or beacon slot.
                            """
                            if node.function.is_reading(slot) or slot.name in node.inline_asm:
                                for asm in asm_split:
                                    if "sstore" in asm:
                                        # print(f"functions_writing_to_variable: found sstore:\n{asm}\n"
                                        #       f"(proxy_features line:{getframeinfo(currentframe()).lineno})")
                                        val_str = asm.split("sstore")[1].split(",")[1].split(")")[0].strip()
                                        # print(val_str)
                                        value_written = node.function.get_local_variable_from_name(val_str)
                                        setters.append([func, value_written])
                                        # print(f"functions_writing_to_variable: {func} writes {value_written}"
                                        #       f" to {slot} w/ sstore"
                                        #       f" (proxy_features line:{getframeinfo(currentframe()).lineno})")
                                        break
                    elif node.type == NodeType.EXPRESSION:
                        exp = node.expression
                        """
                        Only bother extracting the sstore if the function is actually using
                        the implementation slot. Without the line below, this would return any
                        function that uses sstore, even if it is using the admin or beacon slot.
                        """
                        if node.function.is_reading(slot) or slot.name in str(exp):
                            if isinstance(exp, AssignmentOperation):
                                left = exp.expression_left
                                if (str(left) == delegate.name
                                        or (isinstance(left, MemberAccess)
                                            and isinstance(left.expression, CallExpression)
                                            and slot.name in [arg.value.name for arg in left.expression.arguments
                                                              if isinstance(arg, Identifier)])):
                                    """
                                    This case handles the recent versions of ERC-1967 which use the StorageSlot library.
                                    In this case, when extracting the implementation variable during initial analysis,
                                    we encounter the following return statement in the getter:
                                        return StorageSlot.getAddressSlot(_IMPLEMENTATION_SLOT).value;
                                    Due to the complexity of unraveling this expression, we default to returning a new
                                    LocalVariable containing this expression. So in the setter, we expect to find the
                                    following AssignmentOperation:
                                        StorageSlot.getAddressSlot(_IMPLEMENTATION_SLOT).value = newImplementation; 
                                    """
                                    if "sload" in str(exp.expression_right):
                                        continue
                                    value_written = self.get_value_assigned(exp)
                                    setters.append([func, value_written])
                                    # print(f"functions_writing_to_variable: {func} writes {value_written} to {delegate}"
                                    #       f" (proxy_features line:{getframeinfo(currentframe()).lineno})")
                                    break
                            elif isinstance(exp, CallExpression) and str(exp.called).startswith("sstore"):
                                value_written = self.get_value_assigned(exp)
                                setters.append([func, value_written])
                                # print(f"functions_writing_to_variable: {func} writes {value_written} to {slot}"
                                #       f" using sstore (proxy_features line:{getframeinfo(currentframe()).lineno})")
            else:
                for exp in func.all_expressions():
                    if isinstance(exp, AssignmentOperation):
                        left = exp.expression_left
                        right = exp.expression_right
                        if str(left) == delegate.name:
                            value_written = self.get_value_assigned(exp)
                            if value_written is None:
                                dependencies = data_dependency.get_dependencies_recursive(delegate, func.contract)
                                value_written = next((dep for dep in dependencies
                                                      if isinstance(dep, Variable)
                                                      and dep.expression == right))
                            setters.append([func, value_written])
                            # print(f"functions_writing_to_variable: {func} writes {value_written} to {delegate}"
                            #       f" (proxy_features line:{getframeinfo(currentframe()).lineno})")
                            break
                        elif delegate.expression is not None:
                            d_exp = delegate.expression
                            """
                            Code below is necessary in some cases, such as when the delegate is a 
                            LocalVariable with a complicated expression which we were unable to trace
                            to its source. 
                            i.e., for Diamonds this is the value of `delegate`:
                                address facet = ds.selectorToFacetAndPosition[msg.sig].facetAddress;
                            and this is the expression where it is ultimately set, in LibDiamond.addFunction:
                                ds.selectorToFacetAndPosition[_selector].facetAddress = _facetAddress;
                            """
                            if isinstance(d_exp, MemberAccess) and isinstance(left, MemberAccess) \
                                    and d_exp.member_name == left.member_name:
                                member_exp = left
                                d_exp = d_exp.expression
                                left = left.expression
                                if isinstance(d_exp, IndexAccess) and isinstance(left, IndexAccess):
                                    d_exp = d_exp.expression_left
                                    left = left.expression_left
                                    if str(d_exp) == str(left):
                                        value_written = self.get_value_assigned(exp)
                                        setters.append([func, value_written])
                                        # print(f"functions_writing_to_variable: {func} writes {value_written}"
                                        #       f" to {member_exp}"
                                        #       f" (proxy_features line:{getframeinfo(currentframe()).lineno})")
                                        break
        return setters

    def find_diamond_loupe_functions(self) -> Optional[List[Tuple[str, Union[str, "Contract"]]]]:
        """
        For EIP-2535 Diamonds, determine if all four Loupe functions are
        included in any of the "Facet" contracts in the compilation unit.
        These functions are required to be compliant with the standard, and
        it is not sufficient to only include the interface w/o implementations.

        :return: List of (function signature, Contract) pairs indicating
                 which contract contains each of the Loupe functions.
        """
        loupe_facets = []
        loupe_sigs = [
            "facets() returns(IDiamondLoupe.Facet[])",
            "facetAddresses() returns(address[])",
            "facetAddress(bytes4) returns(address)",
            "facetFunctionSelectors(address) returns(bytes4[])"
        ]
        for c in self.compilation_unit.contracts:
            if c == self.contract or c.is_interface:
                continue
            # print(f"Looking for Loupe functions in {c}")
            for f in c.functions:
                # print(f.signature_str)
                if f.signature_str in loupe_sigs:
                    loupe_sigs.remove(f.signature_str)
                    loupe_facets.append((f.signature_str, c))
        if len(loupe_sigs) > 0:
            for sig in loupe_sigs:
                loupe_facets.append((sig, "missing"))
        return loupe_facets

    def can_toggle_delegatecall_on_off(self) -> Tuple[bool, Optional[Expression], Optional[bool], Optional["Node"]]:
        can_toggle = False
        dominators: Optional[Set[Node]] = None
        delegatecall_node: Optional[Node] = None
        alternate_node: Optional[Node] = None
        condition: Optional[Expression] = None
        delegatecall_condition: Optional[bool] = None
        for node in self.contract.fallback_function.all_nodes():
            if node.type == NodeType.ASSEMBLY and isinstance(node.inline_asm, str):
                if "delegatecall" in node.inline_asm:
                    # print(f"can_toggle_delegatecall_on_off: found delegatecall in ASSEMBLY node: {node.inline_asm}")
                    dominators = node.dominators
                    delegatecall_node = node
                    break
            elif node.type == NodeType.EXPRESSION:
                exp = node.expression
                if isinstance(exp, AssignmentOperation):
                    exp = exp.expression_right
                if isinstance(exp, CallExpression) and "delegatecall" in str(exp.called):
                    # print(f"can_toggle_delegatecall_on_off: found delegatecall in EXPRESSION node: {node.inline_asm}")
                    dominators = node.dominators
                    delegatecall_node = node
                    break
        if dominators is not None:
            dom_node = None
            for node in dominators:
                # print(f"can_toggle_delegatecall_on_off:\n"
                #       f" dominator node type: {node.type}\n"
                #       f" dominator expression: {node.expression}")
                # if node.is_conditional(include_loop=False) and all([call not in str(node.expression)
                #                                                     for call in ["require", "assert"]]):
                if node.type == NodeType.IF:
                    condition = node.expression
                    dom_node = node
                    can_toggle = True
                    break
            if dom_node is not None:
                successors = dom_node.dominator_successors_recursive
                # if len(successors) > 0:
                #     print(f"can_toggle_delegatecall_on_off: successors:")
                for successor in successors:
                    # print(f" NodeType: {successor.type}"
                    #       f"  expression: "
                    #       f"{successor.inline_asm if successor.inline_asm is not None else successor.expression}")
                    if successor == delegatecall_node:
                        if successor == dom_node.son_true or dom_node.son_true in successor.dominators:
                            # print(f"can_toggle_delegatecall_on_off: delegatecall_condition = True")
                            delegatecall_condition = True
                        elif successor == dom_node.son_false or dom_node.son_false in successor.dominators:
                            # print(f"can_toggle_delegatecall_on_off: delegatecall_condition = False")
                            delegatecall_condition = False
                if delegatecall_condition is not None:
                    for successor in successors:
                        if successor == delegatecall_node:
                            continue
                        elif ((not delegatecall_condition and (successor == dom_node.son_true or
                                                               dom_node.son_true in successor.dominators))
                              or (delegatecall_condition and (successor == dom_node.son_false or
                                                              dom_node.son_false in successor.dominators))):
                            alternate_node = successor
                            if alternate_node.type in [NodeType.ASSEMBLY, NodeType.PLACEHOLDER] \
                                    or " call(" in str(alternate_node.expression):
                                break
        return can_toggle, condition, delegatecall_condition, alternate_node

    def has_time_delay(self) -> dict:
        if self._has_time_delay is None:
            self._has_time_delay = {"has_delay": False}
            delegate = self._impl_address_variable
            setter = self.contract.proxy_implementation_setter
            condition: Optional[Expression] = None
            if setter is not None:
                for node in setter.all_nodes():
                    if node.expression is not None:
                        exp = node.expression
                        # print(f"has_time_delay: (node.type) {node.type}\n(Expression) {exp}")
                        if isinstance(exp, CallExpression):
                            # print(f"has_time_delay: (node.type) {node.type}\n(CallExpression) {exp}")
                            if str(exp.called) in ["require(bool)", "require(bool,string)", "assert(bool)"]:
                                condition = exp.arguments[0]
                        elif node.type == NodeType.IF:
                            condition = exp
                    if "now" in str(condition) and delegate in [n.expression.expression_left.value
                                                                for n in node.dominator_successors_recursive
                                                                if isinstance(n.expression, AssignmentOperation) and
                                                                isinstance(n.expression.expression_left, Identifier)]:
                        # print(f"has_time_delay: found condition using `now`: {condition}")
                        self._has_time_delay["has_delay"] = True
                        self._has_time_delay["upgrade_condition"] = str(condition)
                        break
                if isinstance(condition, BinaryOperation) and str(condition.type) in ["<", ">", "<=", ">="]:
                    left = condition.expression_left
                    right = condition.expression_right
                    delay_duration = None
                    if "now" in str(left):
                        compare_to_exp = right
                        now_exp = left
                    else:
                        compare_to_exp = left
                        now_exp = right
                    if isinstance(compare_to_exp, BinaryOperation) and str(compare_to_exp.type) == "+":
                        # print(f"has_time_delay: comparing (BinaryOperation) {compare_to_exp} to {now_exp}")
                        compare_to_exp, delay_duration = self.delay_duration_from_binary_operation(compare_to_exp)
                    if isinstance(compare_to_exp, Identifier):
                        # print(f"has_time_delay: comparing (Identifier) {compare_to_exp} to {now_exp}")
                        compare_to_var = compare_to_exp.value
                        self._has_time_delay["timestamp_variable"] = compare_to_var.name
                        timestamp_setters = self.contract.get_functions_writing_to_variable(compare_to_var)
                        self._has_time_delay["timestamp_setters"] = [func.canonical_name for func in timestamp_setters]
                        if delay_duration is None:
                            for func in timestamp_setters:
                                assignment = next((exp for exp in func.expressions
                                                   if isinstance(exp, AssignmentOperation)
                                                   and isinstance(exp.expression_left, Identifier)
                                                   and exp.expression_left.value == compare_to_var
                                                   and "now" in str(exp.expression_right)), None)
                                if assignment is not None:
                                    right = assignment.expression_right
                                    # print(f"has_time_delay: function {func} assigns {right} to {compare_to_var}")
                                    if isinstance(right, BinaryOperation) and str(right.type) == "+":
                                        # print(f"has_time_delay: assigned (BinaryOperation) {right}")
                                        compare_to_exp, delay_duration = self.delay_duration_from_binary_operation(right)
                                        if delay_duration is not None:
                                            break
                    if delay_duration is not None:
                        # print(f"has_time_delay: time delay = {delay_duration}")
                        self._has_time_delay["delay_duration"] = delay_duration
        return self._has_time_delay

    # endregion
    ###################################################################################
    ###################################################################################
    # region Static methods
    ###################################################################################
    ###################################################################################

    @staticmethod
    def delay_duration_from_binary_operation(
            compare_to_exp: Expression
    ) -> Tuple[Expression, Optional[str]]:
        delay_duration = None
        if isinstance(compare_to_exp, BinaryOperation):
            # print(f"delay_duration_from_binary_operation: (BinaryOperation) {compare_to_exp}")
            left = compare_to_exp.expression_left
            right = compare_to_exp.expression_right
            if isinstance(right, Literal):
                # print(f"delay_duration_from_binary_operation: right side (Literal) {right.value}")
                delay_duration = right.value
                if right.subdenomination is not None:
                    delay_duration = f"{delay_duration} {right.subdenomination}"
                if isinstance(left, Identifier):
                    compare_to_exp = left
            elif isinstance(left, Literal):
                delay_duration = left.value
                if left.subdenomination is not None:
                    delay_duration = f"{delay_duration} {left.subdenomination}"
                if isinstance(right, Identifier):
                    compare_to_exp = right
        return compare_to_exp, delay_duration

    @staticmethod
    def is_function_protected_with_comparator(
            function: FunctionContract,
            comparator: str,
            admin_str: Optional[str]
    ) -> Tuple[bool, Optional[str]]:
        check = False

        # print(f"Checking {function.visibility} function {function}")
        for exp in function.all_expressions():
            """
            function.all_expressions() is a recursive getter which includes
            expressions from all functions/modifiers called in given function.
            """
            # if ('msg.sender ' + comparator) in str(exp):
            #     print(f"Found 'msg.sender {comparator}' in expression: {exp}")
            if "require" in str(exp) or "assert" in str(exp):
                """
                'require' and 'assert' are Solidity functions which always
                take a boolean expression as the first argument.
                """
                if isinstance(exp, CallExpression) and len(exp.arguments) > 0:
                    exp = exp.arguments[0]
            if isinstance(exp, Identifier):
                value = ProxyFeatureExtraction.unwrap_identifiers(function.contract, exp)
                if value is None:
                    continue
                exp = value.expression
            if isinstance(exp, BinaryOperation) and str(exp.type) == comparator:
                """
                For this method to return true, we must find a comparison expression,
                i.e., a BinaryOperation, with 'msg.sender' on one side and the
                admin_exp on the other side, where admin_exp must be the same in all.
                """
                if str(exp.expression_left) == "msg.sender":
                    exp = exp.expression_right
                elif str(exp.expression_right) == "msg.sender":
                    exp = exp.expression_left
                else:
                    continue
                if admin_str is None:
                    admin_str = str(exp)
                    check = True
                    break
                elif str(exp) == admin_str:
                    check = True
                    break
        return check, admin_str

    @staticmethod
    def unwrap_identifiers(
            contract: Contract,
            exp: Identifier
    ) -> Optional[Variable]:
        """
        Given an Identifier expression, which is essentially a wrapper for a Variable (or
        sometimes a Function or Contract) object, unwrap it to find the `source` of its value.

        For example, in the expression ``bytes32 slot = IMPLEMENTATION_SLOT`` we have an Identifier
        on either side of the assignment expression. If we passed the left side into this method
        as ``exp``, the first Variable found in ``exp.value`` is the LocalVariable ``slot``. Because
        it is assigned a value in the same line as its declaration, ``exp.value.expression`` is
        the right side of the assignment, which in this case is also an Identifier for the
        StateVariable ``IMPLEMENTATION_SLOT``. But once ``exp`` has been updated to this Identifier,
        then ``exp.value.expression`` is no longer an Identifier, because ``IMPLEMENTATION_SLOT``
        was assigned a value as a Literal expression, namely the 32 byte storage slot.

        Note: This method does not unwrap CallExpressions to find a value's source in another function.
        For example, given the left side of the expression ``address impl = implementation()``,
        ``exp.value`` is the LocalVariable ``impl`` and ``exp.value.expression`` is a CallExpression.
        Tracing this CallExpression to find its return value should be done elsewhere.

        :param contract: The Contract in which the expression is found.
        :param exp: The Identifier expression to unwrap.
        :return: The unwrapped Variable object.
        """
        ret_val = None
        while isinstance(exp, Identifier):
            val = exp.value
            if isinstance(val, SolidityVariable):
                """
                The SolidityVariable class does not inherit Variable, 
                so we cannot immediately set exp = val.expression.
                If the name ends with _slot or _offset, it indicates
                a property of the StateVariable with the same name,
                minus the suffix. The _ here is like dot notation.
                (i.e. delegate_slot = the slot where delegate is stored)
                """
                if val.name.endswith("_slot") or val.name.endswith("_offset"):
                    val = contract.get_state_variable_from_name(val.state_variable)
                else:
                    return ret_val
            ret_val = val
            exp = ret_val.expression
        return ret_val

    @staticmethod
    def check_condition_from_expression(
            condition: Expression,
            in_function: FunctionContract,
            var_written: LocalVariable,
            func_exp_list: List[Tuple[FunctionContract, Expression, bool]],
            original: Optional[Union[CallExpression, ConditionalExpression]]
    ) -> Tuple[Optional[Expression], List[Tuple[FunctionContract, Optional[Expression], bool]]]:
        """
        Helper method specifically intended for use by ``ProxyFeatureExtraction.has_compatibility_checks()``,
        which requires two separate loops to find Solidity function calls and if statements, but which needs
        to perform the same analysis on each condition regardless of which loop finds it.

        Checks whether the condition depends in any way on the same variable that is being written to the
        implementation address variable in a function found by ``Contract.functions_writing_to_delegate()``.

        :param condition: An Expression, extracted either from an if statement condition or from the first
            argument in a call to one of the Solidity functions ``require(bool)``, ``require(bool,string)``
            or ``assert(bool)``.
        :param in_function: The FunctionContract in which this expression was found.
        :param var_written: The LocalVariable being written to the implementation address variable,
            found by ``Contract.functions_writing_to_delegate()``.
        :param func_exp_list: The list of (FunctionContract, Expression) pairs found so far, where Expression
            is a compatibility check found in the FunctionContract, to which to append any newly found checks.
        :param original: The Expression in which the condition expression was found, i.e., a CallExpression
            for require and assert, or a ConditionalExpression in the case of an if condition.
        :return: The full expression in which the compatibility check was found, or None if not found,
            as well as the original list of (FunctionContract, Expression) pairs with any newly found checks
            appended to it.
        """
        check_exp = None
        if var_written is None or (var_written.name not in str(condition)
                                   and not isinstance(condition, Identifier)
                                   and not any([var_written.name in str(call)
                                                for call in in_function.modifier_calls_as_expressions])):
            """
            The boolean result of the condition should depend on the new implementation address value.
            But we need to be careful not to skip cases where the condition is in a modifier.
            """
            return check_exp, func_exp_list
        elif isinstance(condition, Identifier):
            # print(f"check_condition_from_expression: Identifier {condition}")
            if condition.value.expression is not None:
                # print(f"check_condition_from_expression: Identifier.value.expression "
                #       f"{condition.value.expression}")
                condition = condition.value.expression
            else:
                for e in in_function.all_expressions():
                    if isinstance(e, AssignmentOperation) and \
                            str(condition) in str(e.expression_left):
                        condition = e.expression_right
                        break
        # elif len(in_function.modifier_calls_as_expressions) > 0:
        #     print(f"check_condition_from_expression: modifier calls: "
        #           f"{[str(call) for call in in_function.modifier_calls_as_expressions]}")
        call_func = None
        if isinstance(condition, CallExpression):
            """
            i.e., OpenZeppelinUpgradesAddress.isContract(newImplementation)
            Probably need to search this function for the condition it returns.
            What we really want is the BinaryExpression I think.
            """
            called = condition.called
            if isinstance(called, MemberAccess):
                member_of = called.expression
                if isinstance(member_of, Identifier) and isinstance(member_of.value, Contract):
                    call_func = member_of.value.get_function_from_name(called.member_name)
                elif isinstance(member_of, Identifier) and member_of.value == var_written:
                    if isinstance(original, CallExpression):
                        args = [condition]
                        if len(original.arguments) > 1:
                            args.append(original.arguments[1])
                        check_exp = CallExpression(original.called, args, original.type_call)
                        func_exp_list.append((in_function, check_exp, True))
            elif isinstance(called, Identifier) and isinstance(called.value, FunctionContract):
                call_func = called.value
            if isinstance(call_func, FunctionContract) \
                    and "bool" in [str(_type) for _type in call_func.return_type]:
                if call_func.return_node() is not None:
                    ret_exp = call_func.return_node().expression
                    if isinstance(ret_exp, Identifier) and ret_exp.value.expression is not None:
                        ret_exp = ret_exp.value.expression
                    if isinstance(ret_exp, BinaryOperation):
                        condition = ret_exp
        if isinstance(condition, BinaryOperation):
            """
            If either side of the BinaryOperation is a local variable, use the
            expression assigned to it to replace the variable's Identifier.
            i.e., if we have the following:
            function isContract(address account) internal view returns (bool) {
                uint256 size;
                assembly { size := extcodesize(account) }
                return size > 0;
            }
            then we want the final condition expression to be:
                extcodesize(account) > 0
            """
            left = condition.expression_left
            right = condition.expression_right
            if isinstance(left, Identifier):
                if left.value.expression is not None:
                    condition = BinaryOperation(left.value.expression, right, condition.type)
                elif isinstance(left.value, LocalVariable) and isinstance(call_func, FunctionContract):
                    for e in call_func.all_expressions():
                        if isinstance(e, AssignmentOperation) and str(e.expression_left) == str(left):
                            condition = BinaryOperation(e.expression_right, right, condition.type)
            elif isinstance(right, Identifier):
                if right.value.expression is not None:
                    condition = BinaryOperation(left, right.value.expression, condition.type)
                elif isinstance(right.value, LocalVariable) and isinstance(call_func, FunctionContract):
                    for e in call_func.all_expressions():
                        if isinstance(e, AssignmentOperation) and str(e.expression_left) == str(right):
                            condition = BinaryOperation(left, e.expression_right, condition.type)
            # print(f"check_condition_from_expression: condition {condition}")
            if isinstance(original, CallExpression) and call_func is not None:
                args = [condition]
                if len(original.arguments) > 1:
                    args.append(original.arguments[1])
                check_exp = CallExpression(original.called, args, original.type_call)
            elif isinstance(original, ConditionalExpression) and call_func is not None:
                check_exp = ConditionalExpression(condition,
                                                  original.then_expression,
                                                  original.else_expression)
            else:
                check_exp = original
            # print(f"Appending to list: {check_exp} at line ")
            if not (in_function, check_exp, True) in func_exp_list:
                func_exp_list.append((in_function, check_exp, True))
        return check_exp, func_exp_list

    @staticmethod
    def get_value_assigned(exp: Expression) -> Optional[Variable]:
        # print(f"get_value_assigned: {exp}")
        value = None
        id_exp = None
        if isinstance(exp, AssignmentOperation):
            id_exp = exp.expression_right
        elif isinstance(exp, CallExpression) and str(exp.called).startswith("sstore"):
            id_exp = exp.arguments[1]
        while isinstance(id_exp, Identifier):
            value = id_exp.value
            if isinstance(value, Variable):
                id_exp = value.expression
            else:
                break
        return value

    @staticmethod
    def find_slot_string_from_assert(
            proxy: Contract,
            slot: StateVariable
    ):
        slot_string = None
        assert_exp = None
        minus = 0
        if proxy.constructor is not None:
            for exp in proxy.constructor.all_expressions():
                if isinstance(exp, CallExpression) and str(exp.called) == "assert(bool)" and slot.name in str(exp):
                    # print(f"Found assert statement in constructor:\n{str(exp)}")
                    assert_exp = exp
                    arg = exp.arguments[0]
                    if isinstance(arg, BinaryOperation) and str(arg.type) == "==" and arg.expression_left.value == slot:
                        e = arg.expression_right
                        # print("BinaryOperation ==")
                        if isinstance(e, TypeConversion) and str(e.type) == "bytes32":
                            # print(f"TypeConversion bytes32: {str(e)}")
                            e = e.expression
                        if isinstance(e, BinaryOperation) and str(e.type) == "-":
                            # print(f"BinaryOperation -: {str(e)}")
                            if isinstance(e.expression_right, Literal):
                                # print(f"Minus: {str(e.expression_right.value)}")
                                minus = int(e.expression_right.value)
                                e = e.expression_left
                        if isinstance(e, TypeConversion) and str(e.type) == "uint256":
                            # print(f"TypeConversion uint256: {str(e)}")
                            e = e.expression
                        if isinstance(e, CallExpression) and "keccak256(" in str(e.called):
                            # print(f"CallExpression keccak256: {str(e)}")
                            arg = e.arguments[0]
                            if isinstance(arg, Literal):
                                if str(arg.type) == "string":
                                    slot_string = arg.value
                                    break
        return slot_string, assert_exp, minus

    @staticmethod
    def find_mapping_in_var_exp(
            delegate: Variable,
            proxy: Contract
    ) -> (Optional["Variable"], Optional["IndexAccess"]):
        mapping = None
        exp = None
        e = delegate.expression
        if e is not None:
            # print(f"find_mapping_in_var_exp: {delegate} expression is {e}")
            while isinstance(e, TypeConversion) or isinstance(e, MemberAccess):
                e = e.expression
            if isinstance(e, IndexAccess):
                # print(f"find_mapping_in_var_exp: found IndexAccess: {e}")
                exp = e
                left = e.expression_left
                if isinstance(left, MemberAccess):
                    # print(f"find_mapping_in_var_exp: found MemberAccess: {left}")
                    e = left.expression
                    member = left.member_name
                    if isinstance(e, Identifier):
                        # print(f"find_mapping_in_var_exp: found Identifier: {e}")
                        v = e.value
                        if isinstance(v.type, UserDefinedType):
                            user_type: UserDefinedType = v.type
                            # print(f"find_mapping_in_var_exp: found UserDefinedType: {user_type}")
                            if isinstance(user_type.type, Structure):
                                struct: Structure = user_type.type
                                # print(f"find_mapping_in_var_exp: found Structure: {struct.name}")
                                if isinstance(struct.elems[member].type, MappingType):
                                    # print(f"find_mapping_in_var_exp: found mapping in struct: "
                                    #       f"{struct.elems[member].type} {struct.elems[member].name}")
                                    mapping = struct.elems[member]
                elif isinstance(left, Identifier):
                    v = left.value
                    if isinstance(v.type, MappingType):
                        mapping = v
        elif isinstance(delegate.type, MappingType):
            mapping = delegate
            for e in proxy.fallback_function.variables_read_as_expression:
                if isinstance(e, IndexAccess) and isinstance(e.expression_left, Identifier):
                    if e.expression_left.value == mapping:
                        exp = e
                        break
        return mapping, exp

    # endregion
