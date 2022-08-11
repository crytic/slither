from slither import Slither
from slither.detectors.variables import optimize_variable_order

s = Slither('/home/guy/testsol/coolbeans.sol')
s.register_detector(optimize_variable_order.OptimizeVariableOrder)
print(s.run_detectors())