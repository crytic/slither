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


class SpotPriceUsage():
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

    WIKI = "https://github.com/crytic/slither/wiki/Detector-Documentation#oracle-sequencer"

    WIKI_TITLE = "Oracle Sequencer"
    WIKI_DESCRIPTION = "Detection of oracle sequencer."
    WIKI_RECOMMENDATION = "If you deploy contracts on the second layer as Arbitrum, you should perform an additional check if the sequencer is active. For more information visit https://docs.chain.link/data-feeds/l2-sequencer-feeds#available-networks"


    def detect_uniswap_v3(self, function: FunctionContract) -> Node:
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
                    if str(ir.destination.type) == interface_name and ir.function.name == function_name:
                        return True
                elif function_name is None:
                    if ir.destination.type == interface_name:
                        return True
                elif interface_name is None:
                    if ir.function.name == function_name:
                        return True
            
        return False
        
    # def balance_of_usage(self, node_of_pair, ir: Operation) -> bool:
    #     if isinstance(ir, HighLevelCall):
    #         if "ERC20" in ir.destination and ir.function.name == "balanceOf":
    #             if (ir.arguments[0] == node_of_pair):
    #                 return True
    #     return False
    
    # def uniswap_v2_pair(self, node: Node) -> bool:
    #     print(node)
    def wanted_intersting_node_call(self, function: FunctionContract, function_name, interface_name) -> Node:
        for node in function.nodes:
            for ir in node.irs:
                if self.instance_of_call(ir, function_name, interface_name):
                    return node
        return None
                    
            

    def detect_any_fork_of_uniswap(self,function: FunctionContract, found_nodes) -> (Node, str):
        node = self.wanted_intersting_node_call(function, "getReserves", None)
        if node is None:
            node = self.wanted_intersting_node_call(function, "slot0", None)

        for n in found_nodes:
            if (n.node == node):
                return None, None
        return node, "Fork"

        

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
        return spot_price_usage
        
    def generate_informative_messages(self, spot_price_classes):
        messages = []
        for spot_price in spot_price_classes:
            print(spot_price.node)
            print(spot_price.interface)
            if spot_price.interface == "IUniswapV3Pool":
                messages.append(
                    f"Spot price usage detected in Uniswap V3 at {spot_price.node.source_mapping}\n"
                )
            elif spot_price.interface == "IUniswapV2Pair":
                messages.append(
                    f"Spot price usage detected in Uniswap V2 at {spot_price.node.source_mapping}\n"
                )
            else:
                messages.append(
                    f"Spot price usage detected in Uniswap Fork at {spot_price.node.source_mapping}\n"
                )
        return messages

    def _detect(self):
        results = []
        spot_price_usage = self.detect_spot_price_usage()
        if spot_price_usage:
            messages = self.generate_informative_messages(spot_price_usage)
            res = self.generate_result(messages)
            results.append(res)
        return results
