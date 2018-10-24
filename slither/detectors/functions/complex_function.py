from slither.core.declarations.solidity_variables import (SolidityFunction,
                                                          SolidityVariableComposed)
from slither.detectors.abstract_detector import (AbstractDetector,
                                                 DetectorClassification)
from slither.slithir.operations import (HighLevelCall, Index, LowLevelCall, LibraryCall
                                        Send, SolidityCall, Transfer)
from slither.utils.code_complexity import compute_cyclomatic_complexity
from enum import Enum

class COMPLEX(Enum):
        HIGH_EXTERNAL_CALLS = 1
        HIGH_STATE_VARIABLES = 2
        HIGH_CYCLOMATIC_COMPLEXITY = 3

class ComplexFunction(AbstractDetector):
    """

    """

    ARGUMENT = 'complex-function'
    HELP = 'Complex functions'
    IMPACT = DetectorClassification.HIGH
    CONFIDENCE = DetectorClassification.MEDIUM

    MAX_STATE_VARIABLES = 20
    MAX_EXTERNAL_CALLS = 5
    MAX_CYCLOMATIC_COMPLEXITY = 6

    def detect_complex_func(self, func, contract):
        # check the cyclomatic comlexity
        # numerous state vars
        # numerious external calls
        
        """Detect the cyclomatic complexity of the contract functions
        """
        result = []
        code_complexity = compute_cyclomatic_complexity(func)

        if code_complexity > self.MAX_CYCLOMATIC_COMPLEXITY:
            result.append({
                contract: contract,
                func: func,
                type: COMPLEX.HIGH_CYCLOMATIC_COMPLEXITY
            })

        """Detect the number of external calls in the func
           shouldn't be greater than 5
        """
        count = 0
        for node in func.nodes:
            for ir in node.irs:
                if isinstance(ir, (HighLevelCall, LowLevelCall, LibraryCall)):
                    count += 1
                    
        if count > self.MAX_EXTERNAL_CALLS:
            result.append({
                contract: contract,
                func: func,
                type: COMPLEX.HIGH_EXTERNAL_CALLS
            })
            
        return result

    def detect_complex(self, contract):
        ret = []
        
        """Checks the number of the contract state variables if its not greater than 20
        """
        if contract.variables > self.MAX_STATE_VARIABLES:
            ret.append({
                contract: contract,
                type: COMPLEX.HIGH_STATE_VARIABLES
            })
        
        for func in contract.all_functions_called:
            result = self.detect_complex_func(func, contract)
            ret.extend(result)

        return ret
    
    def detect(self):

        for contract in self.contracts:
            
            pass

        pass