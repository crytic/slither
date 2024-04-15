from typing import List
from slither.core.declarations.function_contract import FunctionContract
from slither.detectors.abstract_detector import AbstractDetector
from slither.slithir.operations import HighLevelCall, Operation, LibraryCall
from slither.slithir.variables.variable import Variable
from slither.core.cfg.node import Node
from slither.detectors.abstract_detector import DetectorClassification
from slither.slithir.operations import (
    Binary,
    BinaryType,
)


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
    Documentation
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
    # Uniswap interfaces
    UNISWAP_INTERFACES = ["IUniswapV3Pool", "IUniswapV2Pair"]
    # Suspicious calls for Uniswap
    UNISWAP_SUSPICIOUS_CALLS = ["slot0", "getReserves"]

    # Check if the instance of the call is made, and if the function name and interface name are the same
    # Or if one of them at least matches
    @staticmethod
    def instance_of_call(ir: Operation, function_name, interface_name) -> bool:
        if isinstance(ir, HighLevelCall):
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

    # Get the arguments of the high level call
    @staticmethod
    def get_argument_of_high_level_call(ir: Operation) -> List[Variable]:
        if isinstance(ir, HighLevelCall):
            return ir.arguments
        return []

    # Detect oracle call
    def detect_oracle_call(
        self, function: FunctionContract, function_names, interface_names
    ) -> (Node, str):
        nodes = []
        first_node = None
        second_node = None
        first_arguments = []
        for node in function.nodes:
            for ir in node.irs:
                for i in range(len(function_names)): # pylint: disable=consider-using-enumerate
                    function_name = function_names[i]
                    interface_name = interface_names[i]

                    # Detect UniswapV3 or UniswapV2
                    if self.instance_of_call(ir, function_name, interface_name):
                        nodes.append((node, interface_name))

                    # Detect any fork of Uniswap
                    elif self.instance_of_call(ir, function_name, None):
                        nodes.append((node, None))

                if self.instance_of_call(ir, "balanceOf", None):
                    arguments = self.get_argument_of_high_level_call(ir)
                    if first_node is not None and arguments[0] == first_arguments[0]:
                        second_node = node
                        nodes.append(([first_node, second_node], "BalanceOF"))
                        first_node = None
                        second_node = None
                        first_arguments = []

                    else:
                        first_arguments = arguments
                        first_node = node
                    break

        return nodes

    # Detect spot price usage
    # 1. Detect Uniswap V3
    # 2. Detect Uniswap V2
    # 3. Detect any fork of Uniswap
    # 4. Detect balanceOf method usage which can indicate spot price usage in certain cases
    def detect_spot_price_usage(self):
        spot_price_usage = []
        for contract in self.contracts:
            for function in contract.functions:

                oracle_call = self.detect_oracle_call(
                    function,
                    ["slot0", "getReserves"],
                    ["IUniswapV3Pool", "IUniswapV2Pair"],
                )
                for call in oracle_call:
                    spot_price_usage.append(SpotPriceUsage(call[0], call[1]))

        return spot_price_usage

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
        return False

    # Check if calculations are made with spot data
    def are_calculations_made_with_spot_data(self, node: Node) -> Node:

        # For the case when the node is not a list, create a list
        # This is done to make compatibility with balanceOf method usage which returns two nodes
        if not isinstance(node, list):
            node = [node]

        # Check if the node is used in calculations
        while node:
            variables = node[0].variables_written
            for n in node[0].function.nodes:
                if n == node[0]:
                    continue
                for var in variables:
                    if var in n.variables_read:
                        if self.detect_arithmetic_operations(n):
                            return n
            node.pop()
        return None

    # Generate informative messages for the detected spot price usage
    @staticmethod
    def generate_informative_messages(spot_price_classes):
        messages = []
        for spot_price in spot_price_classes:
            if spot_price.interface == "IUniswapV3Pool":
                messages.append(
                    f"Method which could indicate usage of spot price was detected in Uniswap V3 at {spot_price.node.source_mapping}\n{spot_price.node}\n"
                )
            elif spot_price.interface == "IUniswapV2Pair":
                messages.append(
                    f"Method which could indicate usage of spot price was detected in Uniswap V2 at {spot_price.node.source_mapping}\n{spot_price.node}\n"
                )
            elif spot_price.interface is None:
                messages.append(
                    f"Method which could indicate usage of spot price was detected in Uniswap Fork at {spot_price.node.source_mapping}\n{spot_price.node}\n"
                )
            elif spot_price.interface == "BalanceOF":
                messages.append(
                    f"Method which could indicate usage of spot price was detected at {spot_price.node[0].source_mapping} and {spot_price.node[1].source_mapping}.\n{spot_price.node[0]}\n{spot_price.node[1]}\n"
                )
        return messages

    # Generate message for the node which occured in calculations
    @staticmethod
    def generate_calc_messages(node):
        return f"Calculations are made with spot price data in {node.source_mapping}\n"

    def _detect(self):
        results = []
        spot_price_usage = self.detect_spot_price_usage()
        if spot_price_usage:
            messages = self.generate_informative_messages(spot_price_usage)

            for spot_price in spot_price_usage:
                node = self.are_calculations_made_with_spot_data(spot_price.node)
                if node is not None:
                    self.IMPACT = DetectorClassification.LOW
                    self.CONFIDENCE = DetectorClassification.LOW
                    messages.append(self.generate_calc_messages(node))
            # It can contain duplication, sorted and unique messages.
            # Sorting due to testing purposes
            messages = sorted(list(set(messages)))
            res = self.generate_result(messages)
            results.append(res)
        return results
