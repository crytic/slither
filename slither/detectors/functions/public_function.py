
from slither.analyses.taint.calls import KEY
from slither.analyses.taint.calls import run_taint as run_taint_calls
from slither.analyses.taint.specific_variable import is_tainted
from slither.analyses.taint.specific_variable import \
    run_taint as run_taint_variable
from slither.core.declarations.solidity_variables import (SolidityFunction,
                                                          SolidityVariableComposed)
from slither.detectors.abstract_detector import (AbstractDetector,
                                                 DetectorClassification)
from slither.slithir.operations import (HighLevelCall, Index, LowLevelCall,
                                        Send, SolidityCall, Transfer)

class PublicFunction(AbstractDetector):
    """
    Detect public function that could be declared as external
    """

    ARGUMENT = 'detect-possible-external-function'
    HELP = 'Detect public function that could be declared as external'
    IMPACT = DetectorClassification.HIGH
    CONFIDENCE = DetectorClassification.HIGH

    @staticmethod
    def detect_public_func_declare_external(func):
        pass

    def public_function():
        pass

    def detect(self):
        pass
    

