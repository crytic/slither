from slither.detectors.abstract_detector import AbstractDetector, DetectorClassification
from slither.core.declarations.contract import Contract
from slither.core.declarations.function_contract import FunctionContract

class Oracle:
    def __init__(self, _contract, _function, _interface_var, _line_of_call):
        self.contract = _contract
        self.function = _function
        self.interface_var = _interface_var
        self.line_of_call = _line_of_call # can be get by node.source_mapping.lines[0]
        self.vars_in_condition = []
        self.vars_not_in_condition = []

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
            for function in contract.functions:
                if function.is_constructor:
                    continue
                found_latest_round,name_interface, line = self.latestRoundData(function)
                for var in function.state_variables_read:
                    # print(var.name)
                    # print(var.type)
                    # print(type(var.type))
                    # print("------------------")
                    if (str(var.name) == str(name_interface)) and found_latest_round:
                        oracles.append(Oracle(contract, function, var, line))
                    # if (str(var.type) == "AggregatorV3Interface") and self.check_latestRoundData(function):
                    #     oracles.append(Oracle(contract, function, var)) 
            # print(f.nodes)
        return oracles

    def latestRoundData(self, function: FunctionContract) -> (bool, str,  int):
        for functionCalled in function.external_calls_as_expressions: # Returns tuple (first contract, second function)
            if ("latestRoundData" in str(functionCalled)):
                return (True, str(functionCalled).split(".")[0],  functionCalled.source_mapping.lines[0]) # The external call is in format contract.function, so we split it and get the contract name
        return (False, "", 0)
    
    def get_returned_variables_from_oracle(self, function: FunctionContract, oracle_call_line) -> list:
        returned_vars = []
        for var in function.variables_written:
            if var.source_mapping.lines[0] == oracle_call_line:
                returned_vars.append(var)
        return returned_vars

    def checks_if_vars_in_condition(self, oracle: Oracle,  contract : Contract, function: FunctionContract, oracle_vars) -> bool:
        """
        Detects if vars from oracles are in some condition
        """
        oracle.vars_in_condition = []
        oracle.vars_not_in_condition = []
        for var in oracle_vars:
              if function.is_reading_in_conditional_node(var) or function.is_reading_in_require_or_assert(var):
                    oracle.vars_in_condition.append(var)
              else:
                    oracle.vars_not_in_condition.append(var)

                    
        
    def _detect(self):
        info = []
        oracles = self.chainlink_oracles(self.contracts)
        for oracle in oracles:
            oracle_vars = self.get_returned_variables_from_oracle(oracle.function, oracle.line_of_call)
            if(not self.checks_if_vars_in_condition(oracle, oracle.contract, oracle.function, oracle_vars)):
                rep = "In contract {} a function {} uses oracle {} where the values of vars {} are not checked \n".format(oracle.contract.name, oracle.function.name, oracle.interface_var, [var.name for var in oracle.vars_not_in_condition] )
                info.append(rep)
        res = self.generate_result(info)

        return [res]