from typing import List
from slither.analyses.data_dependency.data_dependency import get_dependencies
from slither.core.declarations.contract import Contract
from slither.core.declarations.function_contract import FunctionContract
from slither.core.variables.state_variable import StateVariable
from slither.detectors.abstract_detector import AbstractDetector
from slither.slithir.operations import HighLevelCall, InternalCall, Operation, Unpack
from slither.slithir.variables.variable import Variable
from slither.core.cfg.node import Node
from slither.detectors.abstract_detector import DetectorClassification
from slither.slithir.operations import (
    Binary,
    BinaryType,
)


# SpotPriceUsage class to store the node and interface
class SpotPriceUsage:
    def __init__(self, node: Node, interface: str):
        self.node = node
        self.interface = interface


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


    def detect_uniswap(self, function: FunctionContract, function_call, interface) -> Node:
        interface = "IUniswapV3Pool"
        function_call = "slot0"
        return self.wanted_intersting_node_call(function, function_call, interface)

    def detect_uniswap_v2(self, function: FunctionContract) -> Node:
        interface = "IUniswapV2Pair"
        function_call = "getReserves"
        return self.wanted_intersting_node_call(function, function_call, interface)
        
    def instance_of_call(self, ir: Operation, function_name, interface_name) -> bool:
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

    def get_argument_of_high_level_call(self, ir: Operation) -> List[Variable]:
        if isinstance(ir, HighLevelCall):
            return ir.arguments
        return []

    def balance_of_spot_price(self, function) -> bool:
        first_node = None
        second_node = None
        first_arguments = []
        for node in function.nodes:
            for ir in node.irs:
                if self.instance_of_call(ir, "balanceOf", None):
                    arguments = self.get_argument_of_high_level_call(ir)
                    if first_node is not None and arguments[0] == first_arguments[0]:
                        second_node = node
                        return first_node, second_node
                    first_arguments = arguments
                    first_node = node
        return first_node, second_node

    def wanted_intersting_node_call(
        self, function: FunctionContract, function_name, interface_name
    ) -> Node:
        for node in function.nodes:
            for ir in node.irs:
                if self.instance_of_call(ir, function_name, interface_name):
                    return node
        return None

    def detect_any_fork_of_uniswap(self, function: FunctionContract, found_nodes) -> (Node, str):
        node = self.wanted_intersting_node_call(function, "getReserves", None)
        if node is None:
            node = self.wanted_intersting_node_call(function, "slot0", None)

        for n in found_nodes:
            if n.node == node:
                return None, None
        return node, "Fork"

    # Detect spot price usage
    # 1. Detect Uniswap V3
    # 2. Detect Uniswap V2
    # 3. Detect any fork of Uniswap
    # 4. Detect balanceOf method usage which can indicate spot price usage in certain cases
    def detect_spot_price_usage(self):
        spot_price_usage = []
        for contract in self.contracts:
            for function in contract.functions:
                node_uniswap_v3 = SpotPriceUsage(self.detect_uniswap_v3(function), "IUniswapV3Pool")
                if node_uniswap_v3.node is not None:
                    spot_price_usage.append(node_uniswap_v3)

                node_uniswap_v2 = SpotPriceUsage(self.detect_uniswap_v2(function), "IUniswapV2Pair")
                if node_uniswap_v2.node is not None:
                    spot_price_usage.append(node_uniswap_v2)

                node_fork = self.detect_any_fork_of_uniswap(function, spot_price_usage)
                node_fork = SpotPriceUsage(node_fork[0], node_fork[1])

                if node_fork.node is not None:
                    spot_price_usage.append(node_fork)

                node1, node2 = self.balance_of_spot_price(function)
                if node1 is not None and node2 is not None:
                    spot_price_usage.append(SpotPriceUsage([node1, node2], "BalanceOF"))

        return spot_price_usage

    def detect_arithmetic_operations(self, node: Node) -> bool:
        for ir in node.irs:
            if isinstance(ir, Binary):
                if ir.type in (
                    BinaryType.ADDITION,
                    BinaryType.SUBTRACTION,
                    BinaryType.MULTIPLICATION,
                    BinaryType.DIVISION,
                ):
                    return True
        return False

    def are_calculations_made_with_spot_data(self, node: Node) -> Node:
        if not isinstance(node, list):
            node = [node]

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

    def generate_informative_messages(self, spot_price_classes):
        messages = []
        for spot_price in spot_price_classes:
            if spot_price.interface == "IUniswapV3Pool":
                messages.append(
                    f"Spot price usage detected in Uniswap V3 at {spot_price.node.source_mapping}\n"
                )
            elif spot_price.interface == "IUniswapV2Pair":
                messages.append(
                    f"Spot price usage detected in Uniswap V2 at {spot_price.node.source_mapping}\n"
                )
            elif spot_price.interface == "Fork":
                messages.append(
                    f"Spot price usage detected in Uniswap Fork at {spot_price.node.source_mapping}\n"
                )
            elif spot_price.interface == "BalanceOF":
                messages.append(
                    f"Spot price usage detected at {spot_price.node[0].source_mapping} and {spot_price.node[1].source_mapping}. It seems like trying to obtain data through balanceOf method.\n"
                )
        return messages

    def generate_calc_messages(self, node):
        return f"Calculations are made with spot price data in {node.source_mapping}\n"

    def _detect(self):
        results = []
        spot_price_usage = self.detect_spot_price_usage()
        if spot_price_usage:
            messages = self.generate_informative_messages(spot_price_usage)

            for spot_price in spot_price_usage:
                node = self.are_calculations_made_with_spot_data(spot_price.node)
                if node is not None:
                    self.IMPACT = DetectorClassification.HIGH
                    messages.append(self.generate_calc_messages(node))
            res = self.generate_result(messages)
            results.append(res)
        return results
