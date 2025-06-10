from slither import Slither
from slither.analyses.data_flow.engine import Engine
from slither.analyses.data_flow.reentrancy import ReentrancyAnalysis

slither = Slither("../contracts/Storage.sol")


functions = [f for c in slither.contracts for f in c.functions]


engine = Engine.new(analysis=ReentrancyAnalysis(), functions=functions)

engine.run_analysis(slither.contracts)
