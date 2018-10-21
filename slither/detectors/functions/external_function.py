
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
from slither.slithir.operations import (InternalCall, InternalDynamicCall)

class ExternalFunction(AbstractDetector):
    """
    Detect public function that could be declared as external
    """

    ARGUMENT = 'detect-external-function'
    HELP = 'Detect public function that could be declared as external'
    IMPACT = DetectorClassification.INFORMATIONAL
    CONFIDENCE = DetectorClassification.HIGH

    @staticmethod
    def detect_external_func(func):
        """ Detect if the function is suicidal

        Detect the public functions that should be declared external

        Checks the following
        * The function is never the destination of an InternalCall
        * There is no InternalDynamicCall (or ensure that the function is never the destination of an InternalDynamicCall)
        * Check if any inherited contracts calls the function


        * Iterate only over the derived contracts (slither.contracts_derived) to be sure that no inherited contract calls the function


        Returns:
            (bool): True if the function is not called
        """

        # check if the function visibility is public
        if func.visibility != 'public':
            return False
        
        # check if the func is not destination of internal call
        if func.
        

        

        pass

    def detect_external(self, contract):
        ret = []
        for f in [f for f in contract.functions if f.contract == contract]:
            if self.detect_external_func(f):
                ret.append(f)
        return ret

    def detect(self):
        result = []

        # check for functions derived contracts call
        for contract in self.slither.contracts_derived:
            pass

        for c in self.contracts:
            functions = self.detect_external(c)
            for func in functions:
                func_name = func.name
                txt = "Public function in {} Contract: {}, Function: {} should be declared external"
                info = txt.format(self.filename,
                                  c.name,
                                  func_name)
                self.log(info)
                results.append({'vuln': 'ExternalFunc',
                                'sourceMapping': func.source_mapping,
                                'filename': self.filename,
                                'contract': c.name,
                                'func': func_name})
        return results