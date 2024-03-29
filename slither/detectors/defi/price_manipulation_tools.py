from typing import List
from slither.detectors.abstract_detector import AbstractDetector, DetectorClassification
from slither.utils.output import Output
from slither.core.declarations import Contract
from slither.core.variables.state_variable import StateVariable
from slither.core.declarations import FunctionContract, Modifier
from slither.core.cfg.node import NodeType, Node
from slither.core.declarations.event import Event
from slither.core.expressions import CallExpression, Identifier
from slither.analyses.data_dependency.data_dependency import is_dependent

from slither.core.declarations.solidity_variables import (
    SolidityFunction,
)
from slither.core.variables.local_variable import LocalVariable
from slither.core.variables.state_variable import StateVariable

from slither.core.expressions import CallExpression
from slither.core.expressions.assignment_operation import AssignmentOperation

from slither.slithir.operations import (
    EventCall,
)
from slither.detectors.defi.price_manipulation_tools import PriceManipulationTools


class PriceManipulationTools:
    # 涉及到资金操作（如转账）的敏感函数，这些函数可能会因为价格操控导致其中参数出现异常从而导致异常资金操作
    DANGEROUS_ERC20_FUNCTION = [
    "transferFrom",
    "safeTransferFrom",
    "mint",
    "burn",
    "burnFrom",
    "transfer",
    "send"
    "safeTransfer",
    "getReward",
    "_transferFrom",
    "_safeTransferFrom",
    "_mint",
    "_burn",
    "_burnFrom",
    "_transfer",
    "_safeTransfer",
    "_getReward",
    "_internalTransfer"
    ]
    UNISWAP_ROUTER_FUNCTION=[
        "_addLiquidity",
        "addLiquidity",
        "removeLiquidity",
        "swapTokensForExactTokens",
        "swapExactTokensForTokens"
    ]
    UNISWAP_PAIR_FUNCTION=[
        "_update",
        "burn",
        "mint",
        "swap",
        "skim"
    ]
    COMMON_FUNCTION = [
        "deposit","withdraw","lending","redeem","borrow","liquidate","claim","getReward"
    ]
    # 喂价函数，仅作为返回值异常检测用
    PRICE_FEED=[
        "eps3ToWant","latestAnswer",
        "extrapolatePoolValueFromToken","getPrice",
        "unsafeValueOfAsset","valueOfAsset"
    ]
    SAFECONTRACTS=["UniswapV2Library","UniswapV2OracleLibrary","UniswapV2Pair","UniswapV2Router02","UniswapV2Factory",
                   "SushiswapV2Factory","SushiswapV2Router02","SushiswapV2Pair","SushiswapV2Library",
                   "SushiSwapProxy","Pair","PancakeLibrary","PancakePair","PancakeRouter","PancakeFactory"]
    