from slither.detectors.abstract_detector import AbstractDetector, DetectorClassification
from slither.core.declarations.contract import Contract
from slither.core.declarations.function_contract import FunctionContract
from slither.core.expressions import expression
from slither.slithir.operations import Condition, Binary, BinaryType

class Oracle:
    def __init__(self, _contract, _function, _interface_var, _line_of_call):
        self.contract = _contract
        self.function = _function
        self.interface_var = _interface_var
        self.line_of_call = _line_of_call # can be get by node.source_mapping.lines[0]
        self.vars_in_condition = []
        self.vars_not_in_condition = []
        self.possible_variables_names = ["price", "timestamp", "updatedAt", "answer", "roundID", "startedAt"]

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
    ORACLE_CALLS = ["latestRoundData", "getRoundData"] # Calls i found which are generally used to get data from oracles, based on docs. Mostly it is lastestRoundData


    def chainlink_oracles(self, contracts: Contract) -> list[Oracle]:
        """
        Detects off-chain oracle contract and VAR
        """
        oracles = []
        for contract in contracts:
            for function in contract.functions:
                if function.is_constructor:
                    continue
                found_latest_round,name_interface, line = self.check_chainlink_call(function)
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

    def compare_chainlink_call(self, function: expression) -> bool:
        for call in self.ORACLE_CALLS:
            if call in str(function):
                return True
        return False
    
    def check_chainlink_call(self, function: FunctionContract) -> (bool, str,  int):
        for functionCalled in function.external_calls_as_expressions:
            if self.compare_chainlink_call(functionCalled):
                return (True, str(functionCalled).split(".")[0],  functionCalled.source_mapping.lines[0]) # The external call is in format contract.function, so we split it and get the contract name
        return (False, "", 0)
    
    def get_returned_variables_from_oracle(self, function: FunctionContract, oracle_call_line) -> list:
        returned_vars = []
        for var in function.variables_written: # This iterates through list of variables which are written in function
            if var.source_mapping.lines[0] == oracle_call_line: # We need to match line of var with line of oracle call
                returned_vars.append(var)
        return returned_vars

    def checks_if_vars_in_condition(self, oracle: Oracle,  contract : Contract, function: FunctionContract, oracle_vars) -> bool:
        """
        Detects if vars from oracles are in some condition
        """
        oracle.vars_in_condition = []
        oracle.vars_not_in_condition = []
        for var in oracle_vars:
              if function.is_reading_in_conditional_node(var) or function.is_reading_in_require_or_assert(var): # These two functions check if within the function some var is in require/assert of in if statement
                    oracle.vars_in_condition.append(var)
              else:
                    oracle.vars_not_in_condition.append(var)
        if len(oracle.vars_not_in_condition) > 0: # If there are some vars which are not in condition, we return false, to indicate that there is a problem
            return False
        return True
    
    def check_var_condition_match(self, var, node) -> bool:
        for var2 in node.variables_read: #This iterates through all variables which are read in node, what means that they are used in condition
            if var.name == var2.name:
                return True
        return False
    

    def check_condition(self,node) -> bool:
        for ir in node.irs:
            if isinstance(ir, Binary):
                if ir.type == BinaryType.LESS or ir.type == BinaryType.LESS_EQUAL: # require(block.timestamp - updatedAt < b)
                    if node.contains_require_or_assert():
                        return 
                    elif node.contains_conditional(): # (if block.timestamp - updatedAt > b) then fail
                        return
                elif ir.type == BinaryType.GREATER or ir.type == BinaryType.GREATER_EQUAL:
                    pass

        return False

    def check_conditions_enough(self, oracle: Oracle) -> bool:
        checks_not_enough = []
        for var in oracle.vars_in_condition:
            for node in oracle.function.nodes:
                if node.is_conditional() and self.check_var_condition_match(var, node):
                    # print(node.slithir_generation)
                    self.check_condition(node)
                    # for ir in node.irs:
                    #     if isinstance(ir, Binary):
                    #         print(ir.type)
                    #         print(ir.variable_left)
                    #         print(ir.variable_right)
                    # print("-----------")

        return checks_not_enough
                    
                    
        
    def _detect(self):
        info = []
        oracles = self.chainlink_oracles(self.contracts)
        for oracle in oracles:
            oracle_vars = self.get_returned_variables_from_oracle(oracle.function, oracle.line_of_call)
            if(not self.checks_if_vars_in_condition(oracle, oracle.contract, oracle.function, oracle_vars)):
                rep = "In contract {} a function {} uses oracle {} where the values of vars {} are not checked \n".format(oracle.contract.name, oracle.function.name, oracle.interface_var, [var.name for var in oracle.vars_not_in_condition] )
                info.append(rep)
            if (len(oracle.vars_in_condition) > 0):
                for var in self.check_conditions_enough(oracle):
                    info.append("Problem with {}",var.name)
        res = self.generate_result(info)

        return [res]