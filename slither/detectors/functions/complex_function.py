from slither.core.declarations.solidity_variables import (SolidityFunction,
                                                          SolidityVariableComposed)
from slither.detectors.abstract_detector import (AbstractDetector,
                                                 DetectorClassification)
from slither.slithir.operations import (HighLevelCall, Index, LowLevelCall,
                                        Send, SolidityCall, Transfer)
from slither.utils.code_complexity import compute_cyclomatic_complexity

class ComplexFunction(AbstractDetector):
    """

    """

    ARGUMENT = 'complex-function'
    HELP = 'Complex functions'
    IMPACT = DetectorClassification.HIGH
    CONFIDENCE = DetectorClassification.MEDIUM    

    def detect_complex_func(self):
        # check the cyclomatic comlexity
        # numerous state vars
        # numerious external calls
        pass

    def detect_complex(self, contract):
        for func in contract.all_functions_called:
            pass

    
    def detect(self):

        for contract in self.contracts:

            pass

        pass