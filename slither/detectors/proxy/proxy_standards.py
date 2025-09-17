from abc import ABC

import hashlib
from slither.detectors.abstract_detector import AbstractDetector, DetectorClassification
from typing import Optional, List, Dict, Callable, Tuple, TYPE_CHECKING, Union
from slither.core.cfg.node import NodeType
from slither.core.declarations.contract import Contract
from slither.core.declarations.structure import Structure
from slither.core.variables.variable import Variable
from slither.core.variables.state_variable import StateVariable
from slither.core.variables.local_variable import LocalVariable
from slither.core.variables.structure_variable import StructureVariable
from slither.core.expressions.identifier import Identifier
from slither.core.expressions.literal import Literal
from slither.core.declarations.function_contract import FunctionContract
from slither.core.expressions.expression import Expression
from slither.core.expressions.call_expression import CallExpression
from slither.core.expressions.type_conversion import TypeConversion
from slither.core.expressions.assignment_operation import AssignmentOperation
from slither.core.expressions.binary_operation import BinaryOperation
from slither.core.expressions.member_access import MemberAccess
from slither.core.expressions.index_access import IndexAccess
from slither.core.solidity_types.mapping_type import MappingType
from slither.core.solidity_types.user_defined_type import UserDefinedType
from slither.core.solidity_types.elementary_type import ElementaryType


class ProxyFeatures(AbstractDetector, ABC):
    ARGUMENT = "proxy-features"
    IMPACT = DetectorClassification.INFORMATIONAL
    CONFIDENCE = DetectorClassification.MEDIUM

    HELP = "Proxy contract does not conform to any known standard"
    WIKI = "https://github.com/crytic/slither/wiki/Upgradeability-Checks#non-standard-proxy"
    WIKI_TITLE = "Proxy Features"

    # region wiki_description
    WIKI_DESCRIPTION = """
Determine whether an upgradeable proxy contract conforms to any known proxy standards, i.e. OpenZeppelin, UUPS, Diamond 
Multi-Facet Proxy, etc.
"""
    # endregion wiki_description

    # region wiki_exploit_scenario
    WIKI_EXPLOIT_SCENARIO = """
```solidity
contract Proxy{
    address logicAddress;

    function() payable {
        logicAddress.delegatecall(msg.data)
    }
}

contract Logic{
    uint variable1;
}
```
The new version, `V2` does not contain `variable1`. 
If a new variable is added in an update of `V2`, this variable will hold the latest value of `variable2` and
will be corrupted.
"""
    # endregion wiki_exploit_scenario

    # region wiki_recommendation
    WIKI_RECOMMENDATION = """
It is better to use one of the common standards for upgradeable proxy contracts. Consider EIP-1967, EIP-1822, EIP-2523, 
or one of the proxy patterns developed by OpenZeppelin.
"""

    # endregion wiki_recommendation

    @staticmethod
    def find_slot_in_setter_asm(
            inline_asm: Union[str, Dict],
            delegate: LocalVariable
    ) -> Optional[str]:
        slot = None
        if "AST" in inline_asm and isinstance(inline_asm, Dict):
            for statement in inline_asm["AST"]["statements"]:
                if statement["nodeType"] == "YulExpressionStatement":
                    statement = statement["expression"]
                if statement["nodeType"] == "YulVariableDeclaration":
                    statement = statement["value"]
                if statement["nodeType"] == "YulFunctionCall":
                    if statement["functionName"]["name"] == "sstore":
                        if statement["arguments"][1] == delegate.name:
                            slot = statement["arguments"][0]
        else:
            asm_split = inline_asm.split("\n")
            for asm in asm_split:
                if "sstore" in asm:
                    params = asm.split("(")[1].strip(")").split(", ")
                    slot = params[0]
        return slot

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
                    print(f"Found assert statement in constructor:\n{str(exp)}")
                    assert_exp = exp
                    arg = exp.arguments[0]
                    if isinstance(arg, BinaryOperation) and str(arg.type) == "==" and arg.expression_left.value == slot:
                        e = arg.expression_right
                        print("BinaryOperation ==")
                        if isinstance(e, TypeConversion) and str(e.type) == "bytes32":
                            print(f"TypeConversion bytes32: {str(e)}")
                            e = e.expression
                        if isinstance(e, BinaryOperation) and str(e.type) == "-":
                            print(f"BinaryOperation -: {str(e)}")
                            if isinstance(e.expression_right, Literal):
                                print(f"Minus: {str(e.expression_right.value)}")
                                minus = int(e.expression_right.value)
                                e = e.expression_left
                        if isinstance(e, TypeConversion) and str(e.type) == "uint256":
                            print(f"TypeConversion uint256: {str(e)}")
                            e = e.expression
                        if isinstance(e, CallExpression) and "keccak256(" in str(e.called):
                            print(f"CallExpression keccak256: {str(e)}")
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
            print(f"{delegate} expression is {e}")
            while isinstance(e, TypeConversion) or isinstance(e, MemberAccess):
                e = e.expression
            if isinstance(e, IndexAccess):
                exp = e
                left = e.expression_left
                if isinstance(left, MemberAccess):
                    e = left.expression
                    member = left.member_name
                    if isinstance(e, Identifier):
                        v = e.value
                        if isinstance(v.type, UserDefinedType) and isinstance(v.type.type, Structure):
                            if isinstance(v.type.type.elems[member].type, MappingType):
                                mapping = v.type.type.elems[member]
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

    def _detect(self):
        results = []
        storage_inheritance_index = None  # Use to ensure
        for contract in self.contracts:
            if contract.is_upgradeable_proxy:
                proxy = contract
                info = [proxy, " appears to ",
                        "maybe " if not contract.is_upgradeable_proxy_confirmed else "",
                        "be an upgradeable proxy contract.\n"]
                json = self.generate_result(info)
                results.append(json)
                delegate = proxy.delegate_variable
                print(f"{proxy.name} delegates to variable of type {delegate.type} called {delegate.name}")

                # Try to extract a mapping from delegate variable
                # If found, this could suggest the proxy implements EIP-1538 or EIP-2535
                mapping, exp = self.find_mapping_in_var_exp(delegate, proxy)
                if mapping is not None and isinstance(mapping.type, MappingType):
                    mtype: MappingType = mapping.type
                    struct = None
                    if isinstance(mapping, StructureVariable):
                        struct = mapping.structure
                    info = [
                        proxy, " stores the values for ", delegate,
                        " in the mapping called ", mapping,
                        " which is located in the structure " if struct is not None else "",
                        struct if struct is not None else "",
                        "\n"
                    ]
                    json = self.generate_result(info)
                    results.append(json)
                    # Extract EIP-2535 Diamond features
                    lib_diamond = proxy.compilation_unit.get_contract_from_name("LibDiamond")
                    if lib_diamond is not None and lib_diamond.get_structure_from_name(
                            "DiamondStorage") is not None:
                        info = [proxy, " appears to be an EIP-2535 Diamond Proxy.\n"]
                        json = self.generate_result(info)
                        results.append(json)
                        # TODO: Determine if the Diamond is upgradeable
                        # i.e., if it adds a DiamondCut facet in constructor
                        # TODO: Determine if the compilation unit contains the required Loupe functions
                    elif str(mtype.type_from) == "bytes4" and str(exp.expression_right) == "msg.sig":
                        info = [proxy, " appears to be an EIP-1538 Transparent Proxy.\n"]
                        json = self.generate_result(info)
                        results.append(json)
                else:
                    print(f"{delegate} expression is None")
                # else:
                #     print(f"{delegate} is a StateVariable")
            elif contract.is_proxy:
                proxy = contract
        return results


class ProxyStandards(ProxyFeatures, ABC):
    ARGUMENT = "proxy-standards"
    IMPACT = DetectorClassification.INFORMATIONAL
    CONFIDENCE = DetectorClassification.MEDIUM

    HELP = "Proxy contract does not conform to any known standard"
    WIKI = "https://github.com/crytic/slither/wiki/Upgradeability-Checks#non-standard-proxy"
    WIKI_TITLE = "Non-Standard Proxy"

    # region wiki_description
    WIKI_DESCRIPTION = """
Determine whether an upgradeable proxy contract conforms to any known proxy standards, i.e. OpenZeppelin, UUPS, Diamond 
Multi-Facet Proxy, etc.
"""
    # endregion wiki_description

    # region wiki_exploit_scenario
    WIKI_EXPLOIT_SCENARIO = """
```solidity
contract Proxy{
    address logicAddress;
    
    function() payable {
        logicAddress.delegatecall(msg.data)
    }
}

contract Logic{
    uint variable1;
}
```
The new version, `V2` does not contain `variable1`. 
If a new variable is added in an update of `V2`, this variable will hold the latest value of `variable2` and
will be corrupted.
"""
    # endregion wiki_exploit_scenario

    # region wiki_recommendation
    WIKI_RECOMMENDATION = """
It is better to use one of the common standards for upgradeable proxy contracts. Consider EIP-1967, EIP-1822, EIP-2523, 
or one of the proxy patterns developed by OpenZeppelin.
"""
    # endregion wiki_recommendation

    def _detect(self):
        results = []
        storage_inheritance_index = None    # Use to ensure
        ProxyFeatures._detect(self)
        for contract in self.contracts:
            if contract.is_upgradeable_proxy:
                proxy = contract
                info = [proxy, " appears to ",
                        "maybe " if not contract.is_upgradeable_proxy_confirmed else "",
                        "be an upgradeable proxy contract.\n"]
                json = self.generate_result(info)
                results.append(json)
                delegate = proxy.delegate_variable
                print(f"{proxy.name} delegates to variable of type {delegate.type} called {delegate.name}")
                lib_diamond = proxy.compilation_unit.get_contract_from_name("LibDiamond")
                ierc_1538 = proxy.compilation_unit.get_contract_from_name("IERC1538")
                if lib_diamond is not None and lib_diamond.get_structure_from_name("DiamondStorage") is not None:
                    info = [proxy, " appears to be an EIP-2535 Diamond Proxy: This is a WIP.\n"]
                    json = self.generate_result(info)
                    results.append(json)
                elif ierc_1538 is not None and ierc_1538 in proxy.inheritance:
                    info = [proxy, " appears to be an EIP-1538 Transparent Proxy:\nThis EIP has been "
                                   "withdrawn and replaced with EIP-2535: Diamonds, Multi-Facet Proxy\n"]
                    json = self.generate_result(info)
                    results.append(json)
                elif isinstance(delegate, StateVariable):
                    print(f"delegate.contract = {delegate.contract}\nproxy = {proxy}")
                    if delegate.contract == proxy:
                        info = [
                            proxy,
                            " stores implementation as state variable: ",
                            delegate,
                            "\nAvoid variables in the proxy. Better to use a standard storage slot, e.g. as proposed in ",
                            "EIP-1967, EIP-1822, Unstructured Storage, Eternal Storage or another well-audited pattern.\n"
                        ]
                        json = self.generate_result(info)
                        results.append(json)
                    elif delegate.contract in proxy.inheritance:
                        print(f"State variable {delegate.name} is in the inherited contract: {delegate.contract.name}")
                        for idx, c in enumerate(proxy.inheritance_reverse):
                            if idx == 0:
                                suffix = "st"
                            elif idx == 1:
                                suffix = "nd"
                            elif idx == 2:
                                suffix = "rd"
                            else:
                                suffix = "th"
                            if c == delegate.contract:
                                info = [
                                    proxy,
                                    " stores implementation as state variable called ",
                                    delegate,
                                    " which is located in the inherited contract called ",
                                    c,
                                    "\nIf this is a storage contract which is shared with the logic contract, it is"
                                    " essential that both have the same order of inheritance, i.e. the storage contract"
                                    " must be the ",
                                    str(idx + 1),
                                    suffix,
                                    " contract inherited, and any preceding inheritances must also be identical.\n"
                                ]
                                json = self.generate_result(info)
                                results.append(json)
                    else:
                        print(f"State variable {delegate.name} is defined in another contract: "
                              f"{delegate.contract.name}")
                        setter = proxy.proxy_implementation_setter
                        getter = proxy.proxy_implementation_getter
                        contract = delegate.contract
                        for c in self.contracts:
                            if contract in c.inheritance:
                                contract = c
                                if setter is not None and isinstance(setter, FunctionContract):
                                    setter.set_contract(c)
                        info = [
                            "The implementation address for ",
                            proxy.name,
                            " is a state variable declared and stored in another contract:\n",
                            delegate.contract
                        ]
                        if contract != delegate.contract:
                            info.append(" which is inherited by ")
                            info.append(contract)
                        if setter is not None:
                            info.append("\nThe implementation setter is: ")
                            info.append(setter)
                        if getter is not None:
                            info.append("\nThe implementation getter is: ")
                            info.append(getter)
                            if delegate.expression is not None:
                                info.append("\nwhich calls " + str(delegate.expression))
                        info.append("\n")
                        json = self.generate_result(info)
                        results.append(json)
                elif isinstance(delegate, LocalVariable) and delegate.location is not None and\
                        "0xc5f16f0fcc639fa48a6947836d9850f504798523bf8c9a3a87d5876cf622bcf7" in str(delegate.location):
                    print(proxy.name + " appears to be an EIP-1822 proxy. Looking for Proxiable contract.")
                    proxiable = proxy.compilation_unit.get_contract_from_name("Proxiable")
                    if proxiable is not None:
                        setter = proxiable.get_function_from_signature("updateCodeAddress(address)")
                        if setter is None:
                            setter = proxiable.get_function_from_signature("_updateCodeAddress(address)")
                        if setter is not None:
                            print(f"Found implementation setter {setter.signature_str}"
                                  f" in contract {proxiable.name}")
                            for c in proxy.compilation_unit.contracts:
                                if c == proxiable:
                                    continue
                                if proxiable in c.inheritance:
                                    print(f"Contract {c.name} inherits {proxiable.name}")
                                    proxiable = c
                            info = [
                                proxy,
                                " appears to be an EIP-1822 Universal Upgradeable Proxy:\nThis proxy doesn't contain"
                                " its own upgrade logic - it is in the logic contract which must inherit Proxiable.\n",
                                proxiable,
                                " appears to be the logic contract used by this proxy.\n"
                            ]
                            json = self.generate_result(info)
                            results.append(json)
                        else:
                            info = [
                                proxy,
                                " appears to be an EIP-1822 Universal Upgradeable Proxy:\nHowever, the Proxiable "
                                "contract ",
                                proxiable,
                                " does not appear to contain the expected implementation setter, updateCodeAddress()."
                                " If this is indeed an EIP-1822 logic contract, then it may no longer be upgradeable!\n"
                            ]
                            json = self.generate_result(info)
                            results.append(json)
                    else:
                        info = [
                            proxy,
                            " appears to be an EIP-1822 Universal Upgradeable Proxy:\nThis proxy doesn't contain"
                            " its own upgrade logic - it is in the logic contract which must inherit Proxiable.\n",
                            "However, the Proxiable contract could not be found in the compilation unit.\n"
                        ]
                        json = self.generate_result(info)
                        results.append(json)
                else:
                    setter = proxy.proxy_implementation_setter
                    slot = proxy.proxy_impl_storage_offset
                    if slot is None:
                        if setter is not None:
                            if isinstance(setter, FunctionContract) and setter.contract != proxy:
                                info = [
                                    "Implementation setter for proxy contract ",
                                    proxy,
                                    " is located in another contract:\n",
                                    setter,
                                    "\n"
                                ]
                                json = self.generate_result(info)
                                results.append(json)
                            if isinstance(delegate, LocalVariable):
                                exp = delegate.expression
                                if exp is not None:
                                    print(exp)
                                else:
                                    for node in setter.all_nodes():
                                        # print(str(node.type))
                                        if node.type == NodeType.VARIABLE:
                                            exp = node.variable_declaration.expression
                                            if exp is not None and isinstance(exp, Identifier):
                                                slot = str(exp.value.expression)
                                                break
                                        # elif node.type == NodeType.EXPRESSION:
                                        #     print(node.expression)
                                        elif node.type == NodeType.ASSEMBLY:
                                            slot = self.find_slot_in_setter_asm(node.inline_asm, delegate)
                                            break
                                    if slot is not None:
                                        print(slot)
                        else:
                            getter = proxy.proxy_implementation_getter
                            exp = None
                            ext_call = None
                            if getter is not None:
                                for node in getter.all_nodes():
                                    # print(node.type)
                                    exp = node.expression
                                    # print(exp)
                                    # if node.expression is not None:
                                    if node.type == NodeType.RETURN and isinstance(exp, CallExpression):
                                        print("This return node is a CallExpression")
                                        if isinstance(exp.called, MemberAccess):
                                            print("The CallExpression is for MemberAccess")
                                            exp = exp.called
                                            break
                                        elif isinstance(node.expression, Identifier):
                                            print("This return node is a variable Identifier")
                                        elif isinstance(node.expression, Expression):
                                            print(node.expression.type)
                                    elif node.type == NodeType.EXPRESSION and isinstance(exp, AssignmentOperation):
                                        left = exp.expression_left
                                        right = exp.expression_right
                                        if isinstance(left, Identifier):
                                            print(f"Left: Identifier {left.type}")
                                        if isinstance(right, CallExpression):
                                            print(f"Right: {right.called}")
                                            if "call" in str(right):
                                                exp = right.called
                                                break
                            if isinstance(exp, MemberAccess):
                                # Getter calls function of another contract in return expression
                                call_exp = exp.expression
                                print(call_exp)
                                call_function = exp.member_name
                                call_contract = None
                                call_type = None
                                if isinstance(call_exp, TypeConversion):
                                    print(f"The getter calls a function from a contract of type {call_exp.type}")
                                    call_type = call_exp.type
                                elif isinstance(call_exp, Identifier):
                                    val = call_exp.value
                                    if isinstance(val, Variable) and str(val.type) == "address" and val.is_constant:
                                        info = [
                                            "Implementation getter for proxy contract ",
                                            proxy,
                                            " appears to make a call to a constant address variable: ",
                                            val,
                                            "\nWithout the Contract associated with this we cannot confirm upgradeability\n"
                                        ]
                                        if "beacon" in val.name.lower():
                                            info.append("However, it appears to be the address of an Upgrade Beacon\n")
                                        json = self.generate_result(info)
                                        results.append(json)
                                if call_type is not None:
                                    call_contract = proxy.compilation_unit.get_contract_from_name(str(call_type))
                                    if call_contract is not None:
                                        print(f"\nFound contract called by proxy: {call_contract.name}")
                                        interface = None
                                        if call_contract.is_interface:
                                            interface = call_contract
                                            call_contract = None
                                            print(f"It's an interface\nLooking for a contract that implements "
                                                  f"the interface {interface.name}")
                                            for c in proxy.compilation_unit.contracts:
                                                if interface in c.inheritance:
                                                    print(f"{c.name} inherits the interface {interface.name}")
                                                    call_contract = c
                                                    break
                                            if call_contract is None:
                                                print(f"Could not find a contract that inherits {interface.name}\n"
                                                      f"Looking for a contract with {call_function}")
                                                for c in self.compilation_unit.contracts:
                                                    has_called_func = False
                                                    if c == interface:
                                                        continue
                                                    for f in interface.functions_signatures:
                                                        if exp.member_name not in f:
                                                            continue
                                                        if f in c.functions_signatures:
                                                            print(f"{c.name} has function {f} from interface")
                                                            has_called_func = True
                                                            break
                                                    if has_called_func:
                                                        print(f"{c.name} contains the implementation getter")
                                                        call_contract = c
                                                        break
                                            if call_contract is None:
                                                print(f"Could not find a contract that implements {exp.member_name}"
                                                      f" from {interface.name}:")
                                            else:
                                                print(f"Looking for implementation setter in {call_contract.name}")
                                                setter = proxy.find_setter_in_contract(call_contract, delegate,
                                                                                       proxy.proxy_impl_storage_offset,
                                                                                       True)
                                                if setter is not None:
                                                    print(f"\nImplementation set by function: {setter.name}"
                                                          f" in contract: {call_contract.name}")
                                                    info = [
                                                        "Implementation setter for proxy contract ",
                                                        proxy,
                                                        " is located in another contract:\n",
                                                        setter,
                                                        "\n"
                                                    ]
                                                    json = self.generate_result(info)
                                                    results.append(json)
                                                    break
                                        if call_contract is not None and not call_contract.is_interface:
                                            contains_getter = False
                                            contains_setter = False
                                            implementation = None
                                            for f in call_contract.functions:
                                                if f.name == exp.member_name:
                                                    for v in f.returns:
                                                        if str(v.type) == "address":
                                                            print(f"Found getter {f.name} in {call_contract.name}")
                                                            contains_getter = True
                                                            call_function = f
                                                            break
                                                    if contains_getter:
                                                        for v in f.variables_read:
                                                            if isinstance(v, StateVariable):
                                                                implementation = v
                                                                break
                                                        break
                                            if contains_getter:
                                                print(f"Looking for implementation setter in {call_contract.name}")
                                                setter = proxy.find_setter_in_contract(call_contract, delegate,
                                                                                       proxy.proxy_impl_storage_offset,
                                                                                       True)
                                                if setter is not None:
                                                    print("Found implementation setter ")
                                                    info = [
                                                        "Implementation setter for proxy contract ",
                                                        proxy,
                                                        " is located in another contract:\n",
                                                        setter,
                                                        "\n"
                                                    ]
                                                    json = self.generate_result(info)
                                                    results.append(json)
                                                    break
                                                else:
                                                    info = [
                                                        "Could not find implementation setter for proxy contract ",
                                                        proxy,
                                                        " which should be located in another contract:\n",
                                                        call_contract,
                                                        "\n"
                                                    ]
                                                    json = self.generate_result(info)
                                                    results.append(json)
                                    else:
                                        print(f"Could not find a contract called {call_type} in compilation unit")
                            elif isinstance(exp, CallExpression):
                                print(f"Not member access, just a CallExpression\n{exp}")
                                exp = exp.called
                                if isinstance(exp, MemberAccess):
                                    print(exp.type)
                                if "." in str(exp):
                                    target = str(exp).split(".")[0]
                    else:
                        print(f"Implementation slot: {slot.name} = {slot.expression}")
                        slot_value = str(slot.expression)
                        slot_string, assert_exp, minus = self.find_slot_string_from_assert(proxy, slot)
                        if slot_string is not None:
                            s = hashlib.sha3_256()
                            # s = sha3.keccak_256()
                            s.update(slot_string.encode("utf-8"))
                            hashed = int("0x" + s.hexdigest(), 16) - minus
                            if int(slot_value, 16) == hashed:
                                print(f"{slot.name} value matches keccak256('{slot_string}')")
                                if slot_string == "eip1967.proxy.implementation":
                                    info = [
                                        proxy,
                                        " implements EIP-1967: Standard Proxy Storage Slots\n"
                                    ]
                                    json = self.generate_result(info)
                                    results.append(json)
                                else:
                                    info = [
                                        proxy,
                                        " uses a proxy implementation storage slot called ",
                                        slot,
                                        " which equals keccack256('",
                                        slot_string,
                                        "')\nHowever it is recommended to use the standard set down by EIP-1967,\ni.e.",
                                        " IMPLEMENTATION_SLOT = bytes32(uint256(keccak256('eip1967.proxy.implementation')) - 1) \n"
                                    ]
                                    json = self.generate_result(info)
                                    results.append(json)
                            else:
                                info = [
                                    "The value of ",
                                    slot.name,
                                    " does not appear to match keccak256('",
                                    slot_string,
                                    "') as required by the assert statement:\n",
                                    str(assert_exp) + "\n"
                                ]
                                json = self.generate_result(info)
                                results.append(json)
                        elif assert_exp is None:
                            info = [
                                "The value of ",
                                slot.name,
                                " does not appear to be checked in the constructor.\n",
                                "When using a hardcoded storage slot, always include an assert statement ",
                                "in the first line of the constructor. For example:\n",
                                "assert(",
                                slot.name,
                                " == keccak256('some.well.defined.string'))\n"
                            ]
                            json = self.generate_result(info)
                            results.append(json)
                    slots = [var for var in proxy.state_variables if var.is_constant and str(var.type) == "bytes32"
                             and "slot" in var.name.lower()]
                    print(f"slots = {slots}")
                    if len(slots) > 1 or (slot is None and len(slots) > 0):
                        info = [
                            proxy,
                            " also uses the following storage slots:\n"
                        ]
                        for s in slots:
                            print(s.name)
                            if s == slot or (slot is not None and s.name == slot.name):
                                continue
                            slot_string, assert_exp, minus = self.find_slot_string_from_assert(proxy, s)
                            if assert_exp is not None:
                                assert_str = str(assert_exp).replace("assert(bool)(", "").replace("))", "')")\
                                    .replace("()(", "('").replace("(bytes)(", "('").replace("==", "=")
                                print(assert_str)
                                info.append(assert_str + "\n")
                            else:
                                info.append(s.name)
                                info.append(((" = " + str(s.expression)) if s.expression is not None else ""))
                                info.append(" (not validated in the constructor!)\n")
                        json = self.generate_result(info)
                        results.append(json)
            elif contract.is_proxy:
                info = [contract, " appears to be a proxy contract, but it doesn't seem to be upgradeable.\n"]
                json = self.generate_result(info)
                results.append(json)
                if contract.delegate_variable is not None:
                    if contract.constructor is not None \
                            and contract.delegate_variable in contract.constructor.variables_written:
                        if contract.delegate_variable.is_immutable:
                            info = [contract, " delegate destination address initialized in Constructor and its type is immutable.\n"]
                            json = self.generate_result(info)
                            results.append(json)
                        else:
                            info = [contract, " delegate destination address initialized in Constructor and its type is regular variable.\n"]
                            json = self.generate_result(info)
                            results.append(json)
                    elif isinstance(contract.delegate_variable.expression, Literal):
                        info = [contract, " delegate destination address is hard-coded in the proxy.\n"]
                        json = self.generate_result(info)
                        results.append(json)
        return results
