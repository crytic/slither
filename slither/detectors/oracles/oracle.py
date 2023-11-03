from slither.detectors.abstract_detector import AbstractDetector, DetectorClassification
from slither.core.declarations.contract import Contract
from slither.core.declarations.function_contract import FunctionContract

class Oracle:
    def __init__(self, _contract, _function, _var):
        self.contract = _contract
        self.function = _function
        self.var = _var

class MyDetector(AbstractDetector):
    """
    Documentation
    """

    ARGUMENT = 'mydetector' # slither will launch the detector with slither.py --detect mydetector
    HELP = 'Help printed by slither'
    IMPACT = DetectorClassification.HIGH
    CONFIDENCE = DetectorClassification.HIGH

    WIKI = 'RUN'

    WIKI_TITLE = 'asda'
    WIKI_DESCRIPTION = 'asdsad'
    WIKI_EXPLOIT_SCENARIO = 'asdsad'
    WIKI_RECOMMENDATION = 'asdsad'
    # https://github.com/crytic/slither/wiki/Python-API
    # def detect_stale_price(Function):
    def chainlink_oracles(self, contracts: Contract) -> list[Oracle]:
        """
        Detects off-chain oracle contract and VAR
        """
        oracles = []
        for contract in contracts:
            if "Oracle" in contract.name:
                for function in contract.functions:
                    if function.is_constructor:
                        continue
                    for var in function.state_variables_read:
                        # print(var.name)
                        # print(var.type)
                        # print(type(var.type))
                        # print("------------------")
                        if (str(var.type) == "AggregatorV3Interface") and self.check_latestRoundData(function):
                            oracles.append(Oracle(contract, function, var)) 
            # print(f.nodes)
        return oracles

    def check_latestRoundData(self, function: FunctionContract) -> bool:
        for functionCalled in function.high_level_calls: # Returns tuple (first contract, second function)
            if str(functionCalled[1].name) == "latestRoundData":
                return True

    def checks_for_timestamp(self, contract : Contract, function: FunctionContract) -> bool:
        """
        Detects timestamp usage
        """
        for var in function.variables_written:
            if ("timestamp" in str(var.name)):
                if function.is_reading_in_conditional_node(var) or function.is_reading_in_require_or_assert(var):
                    return True
        return False
        
    def _detect(self):
        info = []
        oracles = self.chainlink_oracles(self.contracts)
        for oracle in oracles:
            if(not self.checks_for_timestamp(oracle.contract, oracle.function)):
                rep = "Oracle {} in contract {} does not check timestamp\n".format(oracle.function.name, oracle.contract.name)
                info.append(rep)
        res = self.generate_result(info)

        return [res]