from typing import List
from slither import Slither
from slither.analyses.data_flow.engine import Engine
from slither.analyses.data_flow.reentrancy import ReentrancyAnalysis
from slither.core.declarations.function import Function

slither = Slither("../contracts/Reentrancy.sol")

functions: List[Function] = [f for c in slither.contracts for f in c.functions]


engine = Engine.new(analysis=ReentrancyAnalysis(), functions=functions)

engine.run_analysis()
