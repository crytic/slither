from abc import ABC

# import sha3
from slither.detectors.abstract_detector import AbstractDetector, DetectorClassification, SupportedOutput, Output
from slither.detectors.proxy.proxy_features import ProxyFeatureExtraction
from slither.utils.proxy_output import ProxyOutput
from typing import Optional, List, Dict, Callable, Tuple, TYPE_CHECKING, Union
from slither.core.cfg.node import NodeType
from slither.core.declarations.contract import Contract
from slither.core.declarations.structure import Structure
from slither.core.declarations.structure_contract import StructureContract
from slither.core.declarations.modifier import Modifier
from slither.core.variables.variable import Variable
from slither.core.variables.state_variable import StateVariable
from slither.core.variables.local_variable import LocalVariable
from slither.core.variables.structure_variable import StructureVariable
from slither.core.expressions.identifier import Identifier
from slither.core.expressions.literal import Literal
from slither.core.declarations.function_contract import FunctionContract
from slither.core.expressions.call_expression import CallExpression
from slither.core.expressions.type_conversion import TypeConversion
from slither.core.expressions.assignment_operation import AssignmentOperation
from slither.core.expressions.binary_operation import BinaryOperation
from slither.core.expressions.member_access import MemberAccess
from slither.core.expressions.index_access import IndexAccess
from slither.core.solidity_types.mapping_type import MappingType
from slither.core.solidity_types.user_defined_type import UserDefinedType
from slither.core.solidity_types.elementary_type import ElementaryType
from slither.utils.erc import (
    ERC20_all_signatures,
    ERC165_signatures,
    ERC721_all_signatures,
    ERC897_signatures,
    ERC1155_all_signatures
)


class ProxyPatterns(AbstractDetector, ABC):
    ARGUMENT = "proxy-patterns"
    IMPACT = DetectorClassification.INFORMATIONAL
    CONFIDENCE = DetectorClassification.MEDIUM

    HELP = "Proxy contract does not conform to any known standard"
    WIKI = "https://github.com/crytic/slither/wiki/Upgradeability-Checks#proxy-patterns"
    WIKI_TITLE = "Proxy Patterns"

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

    # region custom generate_result
    STANDARD_JSON = False

    """
    Override AbstractDetector.generate_result to define our own json output format
    """

    def generate_result(
            self,
            info: Union[str, List[Union[str, SupportedOutput]]],
            additional_fields: Optional[Dict] = None,
    ) -> ProxyOutput:
        contracts = [i for i in info if isinstance(i, Contract)]
        if len(contracts) > 0:
            contract = contracts[0]
        else:
            contract = None
        output = ProxyOutput(
            contract,
            info,
            additional_fields,
            standard_format=self.STANDARD_JSON,
            markdown_root=self.slither.markdown_root,
        )

        return output

    # endregion
    ###################################################################################
    ###################################################################################
    # region Detect Mappings
    ###################################################################################
    ###################################################################################

    @staticmethod
    def detect_mappings(proxy_features: ProxyFeatureExtraction, delegate: Variable):
        # results = []
        info = []
        features: Dict = {}
        proxy = proxy_features.contract
        """
        Check mapping types, i.e. delegate.type_from and delegate.type_to
        """
        if proxy_features.is_eternal_storage():
            features["eternal_storage"] = True
            info += [
                " uses Eternal Storage\n"
            ]
            # json = self.generate_result(info)
            # results.append(json)
        if isinstance(delegate.type, MappingType):
            if f"{delegate.type.type_from}" == "bytes4":  # and f"{delegate.type.type_to}" == "address":
                """
                Check to confirm that `msg.sig` is used as the key in the mapping
                """
                if proxy_features.is_mapping_from_msg_sig(delegate):
                    features["impl_mapping_from_msg_sig"] = True
                    info += [
                        delegate.name,
                        " maps function signatures to addresses, suggesting multiple implementations.\n"
                    ]
                    # json = self.generate_result(info)
                    # results.append(json)
                    """
                    Check if the mapping is stored in a struct, i.e. DiamondStorage for EIP-2535
                    """
                    if isinstance(delegate, StructureVariable):
                        struct = delegate.structure
                        if struct.name == "DiamondStorage":
                            features["diamond_storage"] = True
                            if struct.canonical_name == "LibDiamond.DiamondStorage":
                                features["diamond_storage_location"] = "LibDiamond (" + str(struct.source_mapping) + ")"
                                features["eip_2535"] = True
                                info += [
                                    delegate.name,
                                    " is stored in the structure specified by EIP-2535: ",
                                    struct.canonical_name,
                                    "\n"
                                ]
                                # json = self.generate_result(info)
                                # results.append(json)
                            elif isinstance(struct, StructureContract):
                                features["diamond_storage_location"] = struct.contract.name + " (" + \
                                                                       str(struct.source_mapping) + ")"
                                features["eip_2535"] = "true (non-standard)"
                                info += [
                                    delegate.name,
                                    " is stored in the structure specified by EIP-2535 but not the one in LibDiamond: ",
                                    struct.canonical_name,
                                    "\n"
                                ]
                                # json = self.generate_result(info)
                                # results.append(json)
                            """
                            Search for the Loupe functions required by EIP-2535.
                            """
                            loupe_facets = proxy_features.find_diamond_loupe_functions()
                            features["diamond_loupe_facets"] = {}
                            for sig, facet in loupe_facets:
                                features["diamond_loupe_facets"][sig] = str(facet)
                            if len(loupe_facets) == 4:
                                info += [
                                    f"Loupe functions located in {', '.join(set(str(c) for f, c in loupe_facets))}\n"
                                ]
                                # json = self.generate_result(info)
                                # results.append(json)
                        else:
                            features["eip_2535"] = False
                            if len(struct.elems) > 1:
                                features["diamond_storage"] = True
                            else:
                                features["diamond_storage"] = False
                            info += [
                                delegate.name,
                                " is stored in a structure: ",
                                struct.canonical_name,
                                ", consistent with Diamond Storage but not EIP-2535\n"
                            ]
                            # json = self.generate_result(info)
                            # results.append(json)
                    else:
                        """
                        Mapping not stored in a struct
                        """
                        features["eip_2535"] = False
                        features["eip_1538"] = True
                else:
                    features["impl_mapping_from_msg_sig"] = "maybe"
                    info += [
                        delegate.name,
                        " probably maps function signatures to addresses, but detector could not find `msg.sig` use.\n"
                    ]
                    # json = self.generate_result(info)
                    # results.append(json)
            else:
                features["impl_mapping_from_msg_sig"] = False
                info += [
                    delegate.name,
                    " is a mapping of type ",
                    str(delegate.type),
                    "\n"
                ]
                # json = self.generate_result(info)
                # results.append(json)
        return info, features

    # endregion
    ###################################################################################
    ###################################################################################
    # region Detect Storage Slot
    ###################################################################################
    ###################################################################################

    @staticmethod
    def detect_storage_slot(proxy_features: ProxyFeatureExtraction):
        # results = []
        info = []
        features: Dict = {}
        proxy = proxy_features.contract
        slot = proxy_features.find_impl_slot_from_sload()
        if slot is not None:
            features["unstructured_storage"] = True
            info += [
                " uses Unstructured Storage\n"
            ]
            # json = self.generate_result(info)
            # results.append(json)
            setter = proxy.proxy_implementation_setter
            if setter is None:
                """
                Use the getter instead
                """
                setter = proxy.proxy_implementation_getter
            if setter is None or setter.contract == proxy or setter.contract in proxy.inheritance:
                if slot == "0x360894a13ba1a3210667c828492db98dca3e2076cc3735a920a3ca505d382bbc" or \
                        slot == "bytes32(uint256(keccak256(bytes)(eip1967.proxy.implementation)) - 1)":
                    features["eip_1967"] = True
                    info += [
                        " implements EIP-1967\n"
                    ]
                    # json = self.generate_result(info)
                    # results.append(json)
                else:
                    features["eip_1967"] = False
                    info += [
                        " uses non-standard slot: ",
                        slot, "\n"
                    ]
                    # json = self.generate_result(info)
                    # results.append(json)
            elif setter.contract != proxy and proxy_features.proxy_only_contains_fallback():
                if slot == "0x360894a13ba1a3210667c828492db98dca3e2076cc3735a920a3ca505d382bbc" or \
                        slot == "bytes32(uint256(keccak256(bytes)(eip1967.proxy.implementation)) - 1)":
                    features["eip_1967"] = True
                    features["eip_1822"] = True
                    info += [
                        " implements EIP-1822 using slot from ERC-1967"
                        " (i.e. OpenZeppelin UUPS)\n"
                    ]
                    # json = self.generate_result(info)
                    # results.append(json)

                elif slot == "0xc5f16f0fcc639fa48a6947836d9850f504798523bf8c9a3a87d5876cf622bcf7":
                    features["eip_1967"] = False
                    features["eip_1822"] = True
                    info += [
                        " implements EIP-1822 (UUPS) with slot = keccak256('PROXIABLE')\n"
                    ]
                    # json = self.generate_result(info)
                    # results.append(json)
                else:
                    features["eip_1967"] = False
                    features["eip_1822"] = False
                    info += [
                        " uses non-standard slot: ",
                        slot, "\n"
                    ]
                    # json = self.generate_result(info)
                    # results.append(json)
        return info, features

    # endregion
    ###################################################################################
    ###################################################################################
    # region Detect Cross-Contract Call
    ###################################################################################
    ###################################################################################

    @staticmethod
    def detect_cross_contract_call(proxy_features: ProxyFeatureExtraction):
        # results = []
        info = []
        features: Dict = {}
        proxy = proxy_features.contract
        delegate = proxy_features.impl_address_variable
        is_cross_contract, call_exp, contract_type = proxy_features.impl_address_from_contract_call()
        if is_cross_contract:
            """
            is_cross_contract is a boolean returned by proxy_features.impl_address_from_contract_call()
            which indicates whether or not a cross contract call was found.
            call_exp is the CallExpression that was found, contract_type is the type of the contract called.
            """
            features["impl_address_from_contract_call"] = str(call_exp)
            info += [
                delegate,
                " gets value from a cross-contract call: ",
                str(call_exp),
                "\n"
            ]
            # json = self.generate_result(info)
            # results.append(json)
            if isinstance(call_exp, CallExpression) and isinstance(contract_type, UserDefinedType):
                """
                We use the presence or absence of arguments in the CallExpression
                to classify the contract as a Registry or a Beacon.
                A Beacon should have no arguments, while a Registry should have at least one.
                Alternatively, if the delegate variable is a mapping in the called contract, it is a Registry.
                """
                if (len(call_exp.arguments) > 0 and str(call_exp.arguments[0]) != "") or \
                        (isinstance(delegate.type, MappingType) and
                         proxy_features.impl_address_location == contract_type.type):
                    rorb = "Registry"
                else:
                    rorb = "Beacon"
                features[rorb.lower()] = contract_type.type.name
                info += [
                    contract_type.type.name,
                    f" appears to be a {rorb} contract for the proxy\n"
                ]
                # json = self.generate_result(info)
                # results.append(json)
                """
                Check where the Registry/Beacon address comes from, 
                i.e. from a storage slot or a state variable
                """
                source = proxy_features.find_registry_address_source(call_exp)
                if source is not None:
                    if isinstance(source, Variable) and source.is_constant and str(source.type) == "bytes32":
                        features[f"{rorb.lower()}_source_type"] = "bytes32 constant storage slot"
                        features[f"{rorb.lower()}_source_slot"] = str(source.expression)
                        info += [
                            "The address of ",
                            contract_type.type.name,
                            " is loaded from storage slot ",
                            source.name,
                            " = ",
                            str(source.expression),
                            "\n"
                        ]
                    elif isinstance(source, StateVariable):
                        features[f"{rorb.lower()}_source_type"] = str(source.type)
                        features[f"{rorb.lower()}_source_variable"] = source.canonical_name
                        info += [
                            "The address of ",
                            contract_type.type.name,
                            " is stored as a state variable: ",
                            source.canonical_name,
                            "\n"
                        ]
                        if source.is_constant:
                            features[f"{rorb.lower()}_source_constant"] = True
                            info += [
                                source.name,
                                f" is constant, so the {rorb} address cannot be upgraded.\n"
                            ]
                        else:
                            features[f"{rorb.lower()}_source_constant"] = False
                            setters = proxy.get_functions_writing_to_variable(source)
                            setters = [setter.canonical_name for setter in setters if not setter.is_constructor]
                            if len(setters) > 0:
                                features[f"{rorb.lower()}_source_setters"] = ", ".join(setters)
                                info += [
                                    source.name,
                                    " can be updated by the following function(s): ",
                                    str(setters),
                                    "\n"
                                ]
                            else:
                                features[f"{rorb.lower()}_source_setters"] = "none found"
                                info += [
                                    "Could not find setter for ",
                                    source.name,
                                    "\n"
                                ]
                    else:
                        features[f"{rorb.lower()}_source_type"] = str(source.type)
                        features[f"{rorb.lower()}_source_variable"] = str(source)
                        info += [
                            "The address of ",
                            contract_type.type.name,
                            " comes from the value of ",
                            source,
                            "\n"
                        ]
                    # json = self.generate_result(info)
                    # results.append(json)
        return info, features

    # endregion
    ###################################################################################
    ###################################################################################
    # region Main _detect
    ###################################################################################
    ###################################################################################

    def _detect(self):
        results = []
        for contract in self.contracts:
            info = []
            features: Dict = {}
            proxy_features = ProxyFeatureExtraction(contract, self.compilation_unit)
            ###################################################################################
            ###################################################################################
            # region Upgradeable Proxy
            ###################################################################################
            ###################################################################################
            if proxy_features.is_upgradeable_proxy:
                proxy = contract
                delegate = proxy_features.impl_address_variable
                info += [proxy,
                         " may be" if not proxy_features.is_upgradeable_proxy_confirmed else " is",
                         " an upgradeable proxy.\n"]
                if contract.is_upgradeable_proxy_confirmed:
                    features["upgradeable"] = True
                else:
                    features["upgradeable"] = "maybe"
                if contract.uses_call_not_delegatecall:
                    features["uses_call_instead_of_delegatecall"] = True
                    info += f"{proxy.name} uses `call` instead of `delegatecall`\n"
                """
                Output the delegate variable and its setter and getter
                """
                if isinstance(delegate, (StateVariable, LocalVariable, StructureVariable)):
                    features["impl_address_variable"] = delegate.canonical_name
                else:
                    features["impl_address_variable"] = delegate.name
                if proxy.proxy_implementation_setter is not None:
                    features["impl_address_setter"] = proxy.proxy_implementation_setter.canonical_name
                else:
                    features["impl_address_setter"] = "not found"
                if proxy.proxy_implementation_getter is not None:
                    features["impl_address_getter"] = proxy.proxy_implementation_getter.canonical_name
                else:
                    features["impl_address_getter"] = "not found"
                # json = self.generate_result(info)
                # results.append(json)
                """
                Check location of implementation address, i.e. contract.delegate_variable.
                Could be located in proxy contract or in a different contract.
                """
                # endregion
                ###################################################################################
                ###################################################################################
                # region Delegate Variable Located in Proxy Contract
                ###################################################################################
                ###################################################################################
                if proxy_features.impl_address_location == proxy:
                    """
                    Check the scope of the implementation address variable,
                    i.e., StateVariable or LocalVariable.
                    """
                    info += [
                        delegate.name,
                        " is declared in the proxy.\n"
                    ]
                    features["impl_address_location"] = proxy.name + " (" + str(proxy.source_mapping) + ")"
                    # json = self.generate_result(info)
                    # results.append(json)

                    # endregion
                    ###################################################################################
                    ###################################################################################
                    # region State Variable
                    ###################################################################################
                    ###################################################################################
                    if isinstance(delegate, StateVariable):
                        """
                        Check the type of the state variable, i.e. an address, a mapping, or something else
                        """
                        features["impl_address_scope"] = "StateVariable"
                        if f"{delegate.type}" == "address":
                            info += [
                                delegate.name,
                                " is an address state variable\n"
                            ]
                            features["impl_address_type"] = "address"
                            # json = self.generate_result(info)
                            # results.append(json)
                            """
                            Check if the implementation address setter is in the proxy contract. 
                            """
                            # if proxy.proxy_implementation_setter is not None:
                            #     if proxy.proxy_implementation_setter.contract == proxy:
                            #         info += [
                            #             "Implementation setter ",
                            #             proxy.proxy_implementation_setter,
                            #             " was found in the proxy contract.\n"
                            #         ]
                            #     else:
                            #         info += [
                            #             "Implementation setter ",
                            #             proxy.proxy_implementation_setter,
                            #             " was found in another contract: ",
                            #             proxy.proxy_implementation_setter.contract,
                            #             "\n"
                            #         ]
                            #     json = self.generate_result(info)
                            #     results.append(json)
                            """
                            Check if logic contract has same variable declared in same slot, i.e. Singleton/MasterCopy
                            """
                            idx, logic = proxy_features.is_impl_address_also_declared_in_logic()
                            if idx >= 0 and logic is not None:
                                features["impl_address_also_declared_in"] = str(logic.source_mapping)
                                features["impl_address_slot"] = str(idx)
                                features["master_copy_coupling"] = True
                                info += [
                                    delegate.name,
                                    " is declared in both the proxy and logic contract (",
                                    logic.name,
                                    f") in storage slot {idx}.\n"
                                ]
                                # json = self.generate_result(info)
                                # results.append(json)
                            elif logic is None:
                                features["master_copy_coupling"] = "missing implementation source"
                        elif f"{delegate.type}" == "bytes32" and delegate.is_constant:
                            # info += self.detect_storage_slot(proxy_features)
                            features["impl_address_type"] = "bytes32 constant storage slot"
                            features["impl_address_slot"] = str(delegate.expression)
                            slot_info, slot_features = self.detect_storage_slot(proxy_features)
                            if len(slot_info) > 0:
                                info += slot_info
                                for key in slot_features.keys():
                                    features[key] = slot_features[key]
                        elif isinstance(delegate.type, MappingType):
                            """
                            Check for mapping results after the else block below, because we want 
                            to check for Eternal Storage regardless of the delegate variable type.
                            i.e. the implementation address may be stored as a StateVariable, but
                            the proxy could still use mappings to store all other variables.
                            """
                            info += [
                                delegate.name,
                                " is a mapping of type ",
                                str(delegate.type),
                                "\n"
                            ]
                            features["impl_address_type"] = str(delegate.type)
                            # json = self.generate_result(info)
                            # results.append(json)
                        else:
                            """
                            Do something else? 
                            Print result for debugging
                            """
                            info += [
                                delegate.name,
                                " is a state variable of type ",
                                str(delegate.type),
                                "\n"
                            ]
                            features["impl_address_type"] = str(delegate.type)
                            # json = self.generate_result(info)
                            # results.append(json)
                        """
                        Check for mappings regardless of delegate.type, 
                        in case EternalStorage is used for variables other than the implementation address.
                        """
                        # info += self.detect_mappings(proxy_features, delegate)
                        map_info, map_features = self.detect_mappings(proxy_features, delegate)
                        if len(map_info) > 0:
                            info += map_info
                            for key in map_features.keys():
                                features[key] = map_features[key]
                    # endregion
                    ###################################################################################
                    ###################################################################################
                    # region Local Variable
                    ###################################################################################
                    ###################################################################################
                    elif isinstance(delegate, LocalVariable):
                        """
                        Check where the local variable gets the value of the implementation address from, i.e., 
                        is it loaded from a storage slot, or by a call to a different contract, or something else?
                        """

                        mapping, exp = ProxyFeatureExtraction.find_mapping_in_var_exp(delegate, proxy)
                        # slot_results = self.detect_storage_slot(proxy_features)
                        if mapping is not None:
                            if isinstance(mapping, StateVariable):
                                features["impl_address_variable"] = f"{mapping.canonical_name}"
                                features["impl_address_scope"] = "StateVariable"
                            elif isinstance(mapping, StructureVariable):
                                features["impl_address_variable"] = f"{mapping.structure.canonical_name}.{mapping.name}"
                                features["impl_address_scope"] = "StructureVariable"
                            features["impl_address_type"] = str(mapping.type)
                            # info += self.detect_mappings(proxy_features, mapping)
                            map_info, map_features = self.detect_mappings(proxy_features, mapping)
                            if len(map_info) > 0:
                                info += map_info
                                for key in map_features.keys():
                                    features[key] = map_features[key]
                        else:
                            features["impl_address_scope"] = "LocalVariable"
                            features["impl_address_type"] = str(delegate.type)
                            slot_info, slot_features = self.detect_storage_slot(proxy_features)
                            if len(slot_info) > 0:
                                info += slot_info
                                for key in slot_features.keys():
                                    features[key] = slot_features[key]
                        """
                        Check for call to a different contract in delegate.expression
                        """
                        # info += self.detect_cross_contract_call(proxy_features)
                        (cross_contract_info,
                         cross_contract_features) = self.detect_cross_contract_call(proxy_features)
                        info += cross_contract_info
                        for key in cross_contract_features.keys():
                            features[key] = cross_contract_features[key]
                    # endregion
                    ###################################################################################
                    ###################################################################################
                    # region Structure Variable
                    ###################################################################################
                    ###################################################################################
                    elif isinstance(delegate, StructureVariable):
                        """
                        Check the type of the structure variable, i.e. an address, a mapping, or something else
                        """
                        struct = delegate.structure
                        features["impl_address_scope"] = "StructureVariable"
                        features["impl_address_in_struct"] = struct.canonical_name
                        if f"{delegate.type}" == "address":
                            features["impl_address_type"] = "address"
                            info += [
                                delegate.name,
                                " is an address stored in a structure: ",
                                struct.canonical_name,
                                "\n"
                            ]
                            # json = self.generate_result(info)
                            # results.append(json)
                        elif isinstance(delegate.type, MappingType):
                            features["impl_address_type"] = str(delegate.type)
                            info += [
                                delegate.name,
                                " is a mapping found in a structure: ",
                                struct.canonical_name,
                                "\n"
                            ]
                            # json = self.generate_result(info)
                            # results.append(json)
                            # info += self.detect_mappings(proxy_features, delegate)
                            map_info, map_features = self.detect_mappings(proxy_features, delegate)
                            if len(map_info) > 0:
                                info += map_info
                                for key in map_features.keys():
                                    features[key] = map_features[key]
                        else:
                            features["impl_address_type"] = str(delegate.type)
                            info += [
                                delegate.name,
                                " is a structure variable of type ",
                                str(delegate.type),
                                " which is unexpected!\n"
                            ]
                            # json = self.generate_result(info)
                            # results.append(json)
                    # endregion
                    else:
                        """
                        Should not be reachable, but print a result for debugging
                        """
                        info += [
                            delegate,
                            " is not a StateVariable, LocalVariable, or StructureVariable."
                            " This should not be possible!\n"
                        ]
                        # json = self.generate_result(info)
                        # results.append(json)
                # endregion
                ###################################################################################
                ###################################################################################
                # region Delegate Variable Located in Different Contract
                ###################################################################################
                ###################################################################################
                else:  # Location of delegate is in a different contract
                    info += [
                        delegate.name,
                        " was found in a different contract.\n"
                    ]
                    features["impl_address_location"] = (proxy_features.impl_address_location.name + " (" +
                                                         str(proxy_features.impl_address_location.source_mapping) + ")")
                    # json = self.generate_result(info)
                    # results.append(json)
                    """
                    Check the scope of the implementation address variable,
                    i.e., StateVariable or LocalVariable.
                    """
                    # endregion
                    ###################################################################################
                    ###################################################################################
                    # region State Variable
                    ###################################################################################
                    ###################################################################################
                    if isinstance(delegate, StateVariable):
                        """
                        Check the type of the state variable, i.e. an address, a mapping, or something else
                        """
                        features["impl_address_scope"] = "StateVariable"
                        if f"{delegate.type}" == "address":
                            features["impl_address_type"] = "address"
                            info += [
                                delegate.name,
                                " is an address state variable.\n"
                            ]
                            # json = self.generate_result(info)
                            # results.append(json)
                        elif f"{delegate.type}" == "bytes32" and delegate.is_constant:
                            features["impl_address_type"] = "bytes32 constant storage slot"
                            features["impl_address_slot"] = str(delegate.expression)
                            # info += self.detect_storage_slot(proxy_features)
                            slot_info, slot_features = self.detect_storage_slot(proxy_features)
                            if len(slot_info) > 0:
                                info += slot_info
                                for key in slot_features.keys():
                                    features[key] = slot_features[key]
                        elif isinstance(delegate.type, MappingType):
                            features["impl_address_type"] = str(delegate.type)
                            info += [
                                delegate.name,
                                " is a mapping of type ",
                                str(delegate.type),
                                "\n"
                            ]
                            # json = self.generate_result(info)
                            # results.append(json)
                        else:
                            """
                            Unexpected variable type
                            Print result for debugging
                            """
                            features["impl_address_type"] = str(delegate.type)
                            info += [
                                delegate.name,
                                " is a state variable of type ",
                                str(delegate.type),
                                "\n"
                            ]
                            # json = self.generate_result(info)
                            # results.append(json)
                        # info += self.detect_mappings(proxy_features, delegate)
                        map_info, map_features = self.detect_mappings(proxy_features, delegate)
                        if len(map_info) > 0:
                            info += map_info
                            for key in map_features.keys():
                                features[key] = map_features[key]
                        """
                        Check if proxy contract makes a call to impl_address_location contract to retrieve delegate
                        """
                        # info += self.detect_cross_contract_call(proxy_features)
                        cross_contract_info, cross_contract_features = self.detect_cross_contract_call(proxy_features)
                        info += cross_contract_info
                        for key in cross_contract_features.keys():
                            features[key] = cross_contract_features[key]
                        """
                        Check if impl_address_location contract is inherited by any contract besides current proxy
                        """
                        for c in self.contracts:
                            if c == proxy or c == proxy_features.impl_address_location:
                                continue
                            if proxy_features.impl_address_location in proxy.inheritance and \
                                    proxy_features.impl_address_location in c.inheritance and \
                                    proxy not in c.inheritance and c not in proxy.inheritance:
                                features["inherited_storage"] = True
                                info += [
                                    " uses Inherited Storage\n"
                                ]
                                # json = self.generate_result(info)
                                # results.append(json)
                                break
                    # endregion
                    ###################################################################################
                    ###################################################################################
                    # region Local Variable
                    ###################################################################################
                    ###################################################################################
                    elif isinstance(delegate, LocalVariable):
                        """
                        Check where the local variable gets the value of the implementation address from, i.e., 
                        is it loaded from a storage slot, or by a call to a different contract, or something else?
                        """
                        features["impl_address_scope"] = "LocalVariable"
                        features["impl_address_type"] = str(delegate.type)
                        mapping, exp = ProxyFeatureExtraction.find_mapping_in_var_exp(delegate,
                                                                                      delegate.function.contract)
                        # info += self.detect_storage_slot(proxy_features)
                        slot_info, slot_features = self.detect_storage_slot(proxy_features)
                        if mapping is not None:
                            features["impl_address_scope"] = "StateVariable"
                            features["impl_address_type"] = str(mapping.type)
                            # info += self.detect_mappings(proxy_features, mapping)
                            map_info, map_features = self.detect_mappings(proxy_features, delegate)
                            if len(map_info) > 0:
                                info += map_info
                                for key in map_features.keys():
                                    features[key] = map_features[key]
                        elif len(slot_info) > 0:
                            info += slot_info
                            for key in slot_features.keys():
                                features[key] = slot_features[key]
                        else:
                            """
                            Check for call to a different contract in delegate.expression
                            """
                            # info += self.detect_cross_contract_call(proxy_features)
                            (cross_contract_info,
                             cross_contract_features) = self.detect_cross_contract_call(proxy_features)
                            info += cross_contract_info
                            for key in cross_contract_features.keys():
                                features[key] = cross_contract_features[key]

                    # endregion
                    ###################################################################################
                    ###################################################################################
                    # region Structure Variable
                    ###################################################################################
                    ###################################################################################
                    elif isinstance(delegate, StructureVariable):
                        """
                        Check the type of the structure variable, i.e. an address, a mapping, or something else
                        """
                        struct = delegate.structure
                        features["impl_address_scope"] = "StructureVariable"
                        features["impl_address_in_struct"] = struct.canonical_name
                        if f"{delegate.type}" == "address":
                            features["impl_address_type"] = "address"
                            info += [
                                delegate.name,
                                " is an address stored in a structure: ",
                                struct.canonical_name,
                                "\n"
                            ]
                            # json = self.generate_result(info)
                            # results.append(json)
                        elif isinstance(delegate.type, MappingType):
                            features["impl_address_type"] = str(delegate.type)
                            info += [
                                delegate.name,
                                " is a mapping found in a structure: ",
                                struct.canonical_name,
                                "\n"
                            ]
                            # json = self.generate_result(info)
                            # results.append(json)
                            # info += self.detect_mappings(proxy_features, delegate)
                            map_info, map_features = self.detect_mappings(proxy_features, delegate)
                            if len(map_info) > 0:
                                info += map_info
                                for key in map_features.keys():
                                    features[key] = map_features[key]
                        else:
                            """
                            Unexpected variable type
                            Print result for debugging
                            """
                            features["impl_address_type"] = str(delegate.type)
                            info += [
                                delegate.name,
                                " is a structure variable of type ",
                                str(delegate.type),
                                " which is unexpected!\n"
                            ]
                            # json = self.generate_result(info)
                            # results.append(json)

                    # endregion
                    else:
                        """
                        Should not be reachable, but print a result for debugging
                        """
                        info += [
                            delegate.name,
                            " is not a StateVariable, a LocalVariable, or a StructureVariable."
                            " This should not be possible!\n"
                        ]
                        # json = self.generate_result(info)
                        # results.append(json)

                # endregion
                ###################################################################################
                ###################################################################################
                # region Transparent Proxy
                ###################################################################################
                ###################################################################################

                """
                Check if the proxy is transparent, i.e., if all external functions other than
                the fallback and receive are only callable by a specific address, and whether 
                the fallback and receive functions are only callable by addresses other than 
                the same specific address
                """
                is_transparent, admin_str = proxy_features.has_transparent_admin_checks()
                if is_transparent:
                    features["transparent"] = True
                    features["external_functions_require_specific_sender"] = True
                    features["fallback_receive_not_callable_by_specific_sender"] = True
                    info += [
                        " uses Transparent Proxy pattern\n"
                    ]
                    # json = self.generate_result(info)
                    # results.append(json)
                else:
                    features["transparent"] = False
                    features["external_functions_require_specific_sender"] = (all(
                        [proxy_features.is_function_protected_with_comparator(fn, "==", admin_str)
                         for fn in proxy.functions if fn.visibility in ["external", "public"]
                         and not fn.is_fallback and not fn.is_receive and not fn.is_constructor]
                    ) and admin_str is not None and not proxy_features.proxy_only_contains_fallback())
                    features["fallback_receive_not_callable_by_specific_sender"] = (all(
                        [proxy_features.is_function_protected_with_comparator(fn, "!=", admin_str)
                         for fn in proxy.functions if fn.is_fallback or fn.is_receive]
                    ) and admin_str is not None)

                # endregion
                ###################################################################################
                ###################################################################################
                # region Compatibility Checks
                ###################################################################################
                ###################################################################################

                """
                Check if all functions that can update the implementation have compatibility checks
                """
                has_checks, func_exp_list = proxy_features.has_compatibility_checks()
                features["compatibility_checks"] = {"has_all_checks": has_checks, "functions": {}}
                # info = []
                if not has_checks:
                    funcs_missing_check = [func for func, check, correct in func_exp_list if check is None]
                    funcs_with_check = [(func, check) for func, check, correct in func_exp_list if check is not None]
                    for func in funcs_missing_check:
                        features["compatibility_checks"]["functions"][func.canonical_name] = "missing"
                        info += [
                            "Missing compatibility check in ",
                            func.canonical_name, "\n"
                        ]
                    for func, check in funcs_with_check:
                        features["compatibility_checks"]["functions"][func.canonical_name] = str(check)
                        info += [
                            "Found compatibility check in ",
                            func.canonical_name,
                            "\n"
                        ]
                elif len(func_exp_list) == 0:
                    features["compatibility_checks"]["functions"] = "no setters found"
                    info += ["No setter functions found to search for compatibility checks.\n"]
                else:
                    info += ["Found compatibility checks in all upgrade functions.\n"]
                    for func, exp, is_correct in func_exp_list:
                        if not is_correct:
                            info += [f"Incorrect compatibility check in {func}: {exp}\n"]
                        features["compatibility_checks"]["functions"][func.canonical_name] = {"check": str(exp),
                                                                                              "is_correct": is_correct}
                # if len(info) > 0:
                # json = self.generate_result(info)
                # results.append(json)

                # endregion
                ###################################################################################
                ###################################################################################
                # region Anti-Pattern Features
                ###################################################################################
                ###################################################################################

                """
                Check whether upgradeability can be removed 
                i.e., if setter is in another contract, which can be updated to remove the setter
                """
                setter = proxy.proxy_implementation_setter
                if setter is not None and setter.contract != proxy and setter.contract not in proxy.inheritance:
                    features["can_remove_upgradeability"] = True
                    """
                    If a beacon or registry was detected earlier, check if its address can be updated
                    """
                    if "beacon_source_constant" in features.keys():
                        if features["beacon_source_constant"]:
                            features["can_remove_upgradeability"] = False
                        elif not features["beacon_source_constant"]:
                            features["can_remove_upgradeability"] = True
                    elif "registry_source_constant" in features.keys():
                        if features["registry_source_constant"]:
                            features["can_remove_upgradeability"] = False
                        elif not features["registry_source_constant"]:
                            features["can_remove_upgradeability"] = True
                    if features["can_remove_upgradeability"]:
                        if "eip_2535" in features.keys():
                            features["how_to_remove_upgradeability"] = f"remove {setter.contract.name} facet"
                            info += [f"To remove upgradeability, delete the {setter.contract.name} facet\n"]
                        else:
                            features["how_to_remove_upgradeability"] = f"remove {setter.name} from {setter.contract}"
                            info += [f"To remove upgradeability, delete {setter.name} from {setter.contract}\n"]
                else:
                    features["can_remove_upgradeability"] = False

                """
                Check whether the proxy can toggle using delegatecall on and off
                """
                can_toggle_delegatecall, condition, delegate_condition, alt_node \
                    = proxy_features.can_toggle_delegatecall_on_off()
                if can_toggle_delegatecall:
                    info += [f"Can toggle delegatecall on/off: condition: {condition}\n"]
                    features["can_toggle_delegatecall"] = True
                    toggle_condition = str(condition)
                    if not delegate_condition:  # condition must equate to False for using delegatecall
                        if "==" in toggle_condition:
                            toggle_condition = toggle_condition.replace("==", "!=")
                        else:
                            toggle_condition = "!" + toggle_condition
                    features["toggle_delegatecall_condition"] = toggle_condition
                    if alt_node.type == NodeType.PLACEHOLDER and isinstance(alt_node.function, Modifier):
                        features["toggle_alternative_logic"] = "placeholder for function with modifier"
                        features["toggle_modifier"] = alt_node.function.name
                    elif alt_node.type == NodeType.ASSEMBLY and " call" in alt_node.inline_asm:
                        features["toggle_alternative_logic"] = "uses call instead of delegatecall"
                    else:
                        alt_logic = str(alt_node.expression) if alt_node.expression is not None else "None"
                        features["toggle_alternative_logic"] = alt_logic
                    if isinstance(condition, Identifier):
                        condition_var = condition.value
                        funcs_writing_condition = proxy.get_functions_writing_to_variable(condition_var)
                        features["toggle_setters"] = [func.name for func in funcs_writing_condition]
                    elif isinstance(condition, BinaryOperation) \
                            and delegate in [exp.value for exp in condition.expressions if isinstance(exp, Identifier)]:
                        features["toggle_setters"] = [proxy.proxy_implementation_setter.name]

                """
                Check whether there are any immutable external/public functions (besides fallback/receive) 
                and see if they contain delegatecall
                """
                if not proxy_features.proxy_only_contains_fallback():
                    features["immutable_functions"] = {}
                    funcs_containing_delegatecall = []
                    for function in proxy.functions:
                        if function.visibility in ["external", "public"]:
                            if function.is_receive or function.is_fallback or function.is_constructor:
                                continue
                            if function.contains_assembly or any([modifier.contains_assembly
                                                                  for modifier in function.modifiers]):
                                asm_nodes = function.assembly_nodes
                                for node in asm_nodes:
                                    if node.inline_asm is not None and "delegatecall" in node.inline_asm:
                                        funcs_containing_delegatecall.append(function.full_name)
                                        features["immutable_functions"]["containing_delegatecall"] \
                                            = funcs_containing_delegatecall
                                        break
                    """
                    Check if the proxy contains any known ERC functions (if it contains external functions)
                    """
                    ERC721 = list(set(ERC721_all_signatures).difference(ERC20_all_signatures + ERC165_signatures))
                    ERC1155 = list(set(ERC1155_all_signatures).difference(ERC20_all_signatures + ERC165_signatures))
                    all_erc_sigs = ERC20_all_signatures + ERC165_signatures + ERC721 + ERC897_signatures + ERC1155
                    if any(function.full_name in all_erc_sigs
                           for function in proxy.functions if function.name != "implementation"):
                        if any(function.full_name in ERC20_all_signatures for function in proxy.functions):
                            erc20_functions = []
                            for sig in ERC20_all_signatures:
                                if proxy.get_function_from_signature(sig) is not None:
                                    erc20_functions.append(sig)
                            features["immutable_functions"]["erc20"] = erc20_functions
                        if any(function.full_name in ERC165_signatures for function in proxy.functions):
                            erc165_functions = []
                            for sig in ERC165_signatures:
                                if proxy.get_function_from_signature(sig) is not None:
                                    erc165_functions.append(sig)
                            features["immutable_functions"]["erc165"] = erc165_functions
                        if any(function.full_name in ERC721 for function in proxy.functions):
                            erc721_functions = []
                            for sig in ERC721_all_signatures:
                                if proxy.get_function_from_signature(sig) is not None:
                                    erc721_functions.append(sig)
                            features["immutable_functions"]["erc721"] = erc721_functions
                        if any(function.full_name in ERC1155 for function in proxy.functions):
                            erc1155_functions = []
                            for sig in ERC1155_all_signatures:
                                if proxy.get_function_from_signature(sig) is not None:
                                    erc1155_functions.append(sig)
                            features["immutable_functions"]["erc1155"] = erc1155_functions
                        # for ERC-897: DelegateProxy, only care if `proxyType()` is present, since
                        # `implementation()` is found in so many proxies which don't use EIP-897
                        if all(function.full_name in ERC897_signatures for function in proxy.functions):
                            features["immutable_functions"]["erc897"] = ERC897_signatures
                    """
                    Add remaining public/external functions not covered above
                    """
                    other_functions = [function.full_name for function in proxy.functions
                                       if function.visibility in ["external", "public"]
                                       and function.full_name not in str(features["immutable_functions"])
                                       and not (function.is_constructor or function.is_fallback or function.is_receive)]
                    if len(other_functions) > 0:
                        features["immutable_functions"]["other"] = other_functions

                """
                TODO: Check whether upgrading has a time-delay
                """
                has_time_delay = proxy_features.has_time_delay()
                if has_time_delay["has_delay"]:
                    features["time_delay"] = has_time_delay

                # endregion
            ###################################################################################
            ###################################################################################
            # region Non-Upgradeable Proxy
            ###################################################################################
            ###################################################################################

            elif contract.is_proxy:
                """
                Contract is either a non-upgradeable proxy, or upgradeability could not be determined
                """
                info += [contract, " is a proxy, but doesn't seem upgradeable.\n"]
                features["upgradeable"] = False

            # endregion
            else:
                continue
            json = self.generate_result(info, features)
            results.append(json)
        return results
    # endregion
