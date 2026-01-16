from typing import List, Tuple
from slither.core.declarations.function_contract import FunctionContract
from slither.detectors.abstract_detector import AbstractDetector
from slither.slithir.operations import HighLevelCall, Operation, LibraryCall, Assignment
from slither.analyses.data_dependency.data_dependency import is_dependent
from slither.slithir.variables.variable import Variable
from slither.core.cfg.node import Node, recheable, NodeType
from slither.detectors.abstract_detector import DetectorClassification
from slither.slithir.operations import (
    Binary,
    BinaryType,
)

from slither.core.declarations.function import Function


# SpotPriceUsage class to store the node and interface
# For better readability of messages
class SpotPriceUsage:
    def __init__(self, node: Node, interface: str):
        self.node = node
        self.interface = interface

    def mapping(self):
        return self.node.source_mapping

    def type_of_interface(self):
        return self.interface


class SpotPriceDetector(AbstractDetector):
    """
    Documentation: This detector is used to detect the usage of spot price in the contract.
    """

    ARGUMENT = (
        "oracle-spot-price"  # slither will launch the detector with slither.py --detect mydetector
    )
    HELP = "Oracle vulnerabilities"
    IMPACT = DetectorClassification.INFORMATIONAL
    CONFIDENCE = DetectorClassification.INFORMATIONAL

    WIKI = "https://github.com/crytic/slither/wiki/Detector-Documentation#oracle-spot-price"

    WIKI_TITLE = "Oracle Spot prices"
    WIKI_DESCRIPTION = "Detection of spot price usage"
    WIKI_RECOMMENDATION = "Using spot price for calculations can lead to vulnerabilities. Make sure to validate the data before using it or consider use of TWAP oracles."

    # SafeMath functions for compatibility with solidity contracts < 0.8.0 version
    SAFEMATH_FUNCTIONS = ["mul", "div"]
    # Uniswap calculations functions
    CALC_FUNCTIONS = ["getAmountOut", "getAmountsOut"]
    # Protected functions -> Indicating TWAP V2 oracles
    PROTECTED_FUNCTIONS = [
        "currentCumulativePrices",
        "price1CumulativeLast",
        "price0CumulativeLast",
    ]
    # Uniswap interfaces
    UNISWAP_INTERFACES = ["IUniswapV3Pool", "IUniswapV2Pair"]
    # Suspicious calls for Uniswap
    UNISWAP_SUSPICIOUS_CALLS = ["slot0", "getReserves"]

    # Check if the instance of the call is made, and if the function name and interface name are the same
    # Or if one of them at least matches
    @staticmethod
    def instance_of_call(ir: Operation, function_name, interface_name) -> bool:
        if isinstance(ir, HighLevelCall):
            if not hasattr(ir.function, "name") or not hasattr(ir.destination, "type"):
                return False
            if isinstance(ir.destination, Variable):
                if function_name is not None and interface_name is not None:
                    if (
                        str(ir.destination.type) == interface_name
                        and ir.function.name == function_name
                    ):
                        return True
                elif function_name is None:
                    if str(ir.destination.type) == interface_name:
                        return True
                elif interface_name is None:
                    if ir.function.name == function_name:
                        return True

        return False

    # Ignore functions related to calculation of TWAP
    def ignore_function(self, ir) -> bool:
        for function in self.PROTECTED_FUNCTIONS:
            if self.instance_of_call(ir, function, None):
                return True
        return False

    # Get the arguments of the high level call
    @staticmethod
    def get_argument_of_high_level_call(ir: Operation) -> List[Variable]:
        if isinstance(ir, HighLevelCall):
            return ir.arguments
        return []

    @staticmethod
    def different_address(first_ir: Operation, second_ir: Operation) -> bool:
        if (
            hasattr(first_ir, "destination")
            and hasattr(second_ir, "destination")
            and first_ir.destination != second_ir.destination
        ):
            return True
        return False

    def detect_oracle_call(
        self, function: FunctionContract, function_names: List[str], interface_names: List[str]
    ) -> Tuple[List[Tuple[Node, str]], List[Node]]:
        """Detect oracle calls in a function."""
        nodes: List[Tuple[Node, str]] = []
        first_node = None
        first_arguments: List = []
        swap_indicators: List[Node] = []
        counter = 0
        for node in function.nodes:
            for ir in node.irs:
                for function_name, interface_name in zip(function_names, interface_names):
                    if self.ignore_function(ir):
                        return ([], [])
                    # Detect UniswapV3 or UniswapV2
                    if self.instance_of_call(ir, function_name, interface_name):
                        if interface_name == "IUniswapV3Pool" and not self.slot0_returned_price(
                            node.variables_written
                        ):
                            continue
                        nodes.append((node, interface_name))

                    # Detect any fork of Uniswap
                    elif self.instance_of_call(ir, function_name, None):
                        if interface_name == "IUniswapV3Pool" and not self.slot0_returned_price(
                            node.variables_written
                        ):
                            continue
                        nodes.append((node, interface_name))

                    # Swap indication
                    elif self.instance_of_call(ir, "swap", None):
                        swap_indicators = [node]

                # Detection of balanceOf spot price pattern
                if self.instance_of_call(ir, "balanceOf", None):
                    arguments = self.get_argument_of_high_level_call(ir)
                    # Node need to be set and argument of the call need to be the same as the first one
                    if (
                        first_node is not None
                        and arguments[0] == first_arguments[0]
                        and self.different_address(first_node[1], ir)
                        and counter == 1
                    ):
                        nodes.append(([first_node[0], node], "BalanceOF"))
                        first_node = None
                        first_arguments = []

                    else:
                        first_arguments = arguments  # Store arguments for comparison
                        first_node = (
                            node,
                            ir,
                        )  # Node and ir which stores destination can be used for address var comparison
                        counter = 0
                    break
                # Counter used to check if the next node is immediately after the first node to follow pattern
                counter += 1

        return nodes, swap_indicators

    # Detect spot price usage
    # 1. Detect Uniswap V3
    # 2. Detect Uniswap V2
    # 3. Detect any fork of Uniswap
    # 4. Detect balanceOf method usage which can indicate spot price usage in certain cases
    def detect_spot_price_usage(self):
        spot_price_usage = []
        swap_functions = []
        for contract in self.contracts:
            for function in contract.functions:
                oracle_calls, swap_function = self.detect_oracle_call(
                    function,
                    ["slot0", "getReserves"],
                    ["IUniswapV3Pool", "IUniswapV2Pair"],
                )
                uniswap = False
                for call in oracle_calls:
                    spot_price_usage.append(SpotPriceUsage(call[0], call[1]))
                    if call[1] in self.UNISWAP_INTERFACES:
                        uniswap = True
                if uniswap and swap_function:
                    swap_functions.append(function)
        return spot_price_usage, swap_functions

    # Check if arithmetic operations are made
    # Compatibility with SafeMath library
    def detect_arithmetic_operations(self, node: Node) -> bool:
        for ir in node.irs:
            if isinstance(ir, Binary):
                if ir.type in (
                    BinaryType.MULTIPLICATION,
                    BinaryType.DIVISION,
                ):
                    return True
            elif isinstance(ir, LibraryCall):
                if hasattr(ir, "function"):
                    if ir.function.name in self.SAFEMATH_FUNCTIONS:
                        return True
            # if arithmetic_op:
            #     if "FixedPoint.fraction" in str(node):
            #         return False
        return False

    def calc_functions(self, node: Node) -> bool:
        for ir in node.irs:
            if isinstance(ir, HighLevelCall):
                if ir.function.name in self.CALC_FUNCTIONS:
                    return True
        return False

    # Check if slot0 returned price value
    @staticmethod
    def slot0_returned_price(variables) -> bool:
        for var in variables:
            # sqrtPricex96 is type uint160 and only var of this type is returned by slot0
            if hasattr(var, "type") and str(var.type) == "uint160":
                return True
        return False

    @staticmethod
    def check_reserve_var(var) -> bool:
        """Check if var is a reserve variable (uint112 or uint256 type)."""
        return hasattr(var, "type") and (str(var.type) == "uint112" or str(var.type) == "uint256")

    @staticmethod
    def track_var(variable, node):
        """Track if the variable was assigned to a different variable without change."""
        temp_variable = None
        for ir in node.irs:
            if isinstance(ir, Assignment):
                if str(ir.rvalue) == str(variable):
                    temp_variable = ir.lvalue
            else:
                return variable
        if temp_variable is not None:
            for v in node.variables_written:
                if str(v) == str(temp_variable):
                    variable = v
        return variable

    @staticmethod
    # Check if calculations are linked to return, that would indicate only get/calculation function
    def are_calcs_linked_to_return(node: Node) -> bool:
        function = node.function
        variables = node.variables_written
        returned_vars = function.returns
        for r_var in returned_vars:
            for var in variables:
                if is_dependent(r_var, var, function):
                    return function
        if node.type == NodeType.RETURN:
            return function
        for s in node.sons:
            if s.type == NodeType.RETURN:
                return function
        return None

    # Check if calculations are made with spot data
    def are_calculations_made_with_spot_data(self, node: Node, interface: str) -> Node:
        # For the case when the node is not a list, create a list
        # This is done to make compatibility with balanceOf method usage which returns two nodes
        if not isinstance(node, list):
            node = [node]

        # Check if the node is used in calculations
        nodes = []
        return_functions = []

        # Loop because of BalanceOF method usage as it returns two nodes
        while node:
            variables = node[0].variables_written
            recheable_nodes = recheable(node[0])
            changed_vars = []
            # Track the variable if it was assigned to different variable without change
            for n in recheable_nodes:
                for var in variables:
                    changed_vars.append(self.track_var(var, n))
            # Check if the variable is used in arithmetic operations or calculate function
            for n in recheable_nodes:
                for var in changed_vars:
                    if var in n.variables_read:
                        if interface == "IUniswapV2Pair" and not self.check_reserve_var(var):
                            continue
                        # Check if the variable is used in arithmetic operations
                        if self.detect_arithmetic_operations(n):
                            nodes.append(n)
                        # Check if the variable is used in calculation functions
                        elif self.calc_functions(n):
                            nodes.append(n)
            node.pop()
        # Check if the spot price data are returned
        for node2 in nodes:
            function = self.are_calcs_linked_to_return(node2)
            return_functions.append(function)
        return nodes, return_functions

    # Check if the function, where the spot price data is obtained is used anywhere
    @staticmethod
    def only_return(function: Function) -> bool:
        if function is None:
            return False

        if (function.view or function.pure) and not function.reachable_from_functions:
            return True

        return False

    # Generate informative messages for the detected spot price usage
    @staticmethod
    def generate_informative_messages(spot_price_classes, swap_functions):
        messages = []
        additional_message = ""
        # Iterate through all spot price method occuriences
        for spot_price in spot_price_classes:
            if not isinstance(spot_price.node, list):
                node = [spot_price.node]
            else:
                node = spot_price.node
            # Check if the function is in the swap functions
            # Statement add for informative purposes
            for function in swap_functions:
                if node[0].function == function:
                    additional_message = " inside function where performed swap operation"
            if spot_price.interface == "IUniswapV3Pool":
                messages.append(
                    f"Method which could indicate usage of spot price was detected in Uniswap V3 at {spot_price.node.source_mapping}{additional_message}\n{spot_price.node}\n"
                )
            elif spot_price.interface == "IUniswapV2Pair":
                messages.append(
                    f"Method which could indicate usage of spot price was detected in Uniswap V2 at {spot_price.node.source_mapping}{additional_message}\n{spot_price.node}\n"
                )
            elif spot_price.interface is None:
                messages.append(
                    f"Method which could indicate usage of spot price was detected in Uniswap Fork at {spot_price.node.source_mapping}{additional_message}\n{spot_price.node}\n"
                )
            elif spot_price.interface == "BalanceOF":
                messages.append(
                    f"Method which could indicate usage of spot price was detected at {spot_price.node[0].source_mapping} and {spot_price.node[1].source_mapping}.\n{spot_price.node[0]}\n{spot_price.node[1]}\n"
                )
            additional_message = ""
        return messages

    # Generate message for the node which occured in calculations
    @staticmethod
    def generate_calc_messages(node: Node, only_return: bool) -> str:
        if only_return:
            return f"Calculations are made with spot price data in {node.source_mapping} but the function is not used anywhere in the contract.\n"

        return f"Calculations are made with spot price data in {node.source_mapping}\n"

    def _detect(self):
        results = []
        spot_price_usage, swap_functions = self.detect_spot_price_usage()
        if spot_price_usage:
            messages = self.generate_informative_messages(spot_price_usage, swap_functions)

            for spot_price in spot_price_usage:
                nodes, return_functions = self.are_calculations_made_with_spot_data(
                    spot_price.node, spot_price.interface
                )
                if nodes:
                    for calc_node, return_func in zip(nodes, return_functions):
                        only_return = self.only_return(return_func)
                        messages.append(self.generate_calc_messages(calc_node, only_return))

            # It can contain duplication, sorted and unique messages.
            # Sorting due to testing purposes
            messages = sorted(list(set(messages)))
            res = self.generate_result(messages)
            results.append(res)
        return results
