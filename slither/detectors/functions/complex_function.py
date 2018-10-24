from slither.core.declarations.solidity_variables import (SolidityFunction,
                                                          SolidityVariableComposed)
from slither.detectors.abstract_detector import (AbstractDetector,
                                                 DetectorClassification)
from slither.slithir.operations import (HighLevelCall, Index, LowLevelCall, LibraryCall
                                        Send, SolidityCall, Transfer)
from slither.utils.code_complexity import compute_cyclomatic_complexity
from enum import Enum

class Complex(Enum):
    HIGH_EXTERNAL_CALLS = 1
    HIGH_STATE_VARIABLES = 2
    HIGH_CYCLOMATIC_COMPLEXITY = 3

    MAX_STATE_VARIABLES = 20
    MAX_EXTERNAL_CALLS = 5
    MAX_CYCLOMATIC_COMPLEXITY = 6

class ComplexFunction(AbstractDetector):
    """

    """

    ARGUMENT = 'complex-function'
    HELP = 'Complex functions'
    IMPACT = DetectorClassification.HIGH
    CONFIDENCE = DetectorClassification.MEDIUM

    def detect_complex_func(self, func, contract):        
        """Detect the cyclomatic complexity of the contract functions
        """
        result = []
        code_complexity = compute_cyclomatic_complexity(func)

        if code_complexity > Complex.MAX_CYCLOMATIC_COMPLEXITY.value:
            result.append({
                contract: contract,
                func: func,
                type: Complex.HIGH_CYCLOMATIC_COMPLEXITY
            })

        """Detect the number of external calls in the func
           shouldn't be greater than 5
        """
        count = 0
        for node in func.nodes:
            for ir in node.irs:
                if isinstance(ir, (HighLevelCall, LowLevelCall, LibraryCall)):
                    count += 1

        if count > Complex.MAX_EXTERNAL_CALLS.value:
            result.append({
                contract: contract,
                func: func,
                type: Complex.HIGH_EXTERNAL_CALLS
            })
        
        """Checks the number of the state variables written to isn't
           greater than 20
        """
        if func.state_variables_written.length > Complex.MAX_STATE_VARIABLES.value:
            ret.append({
                contract: contract,
                func: func
                type: Complex.HIGH_STATE_VARIABLES
            })

        return result

    def detect_complex(self, contract):
        ret = []
        
        for func in contract.all_functions_called:
            result = self.detect_complex_func(func, contract)
            ret.extend(result)

        return ret
    
    def detect(self):
        result = []
        for contract in self.contracts:
            complex_issues = self.detect_complex(contract)
            for issue in complex_issues:
                txt = ""
                
                if issue.type == Complex.HIGH_EXTERNAL_CALLS:
                    txt = "High external calls, complex function in {} Contract: {}, Function: {}"
                if issue.type == Complex.HIGH_CYCLOMATIC_COMPLEXITY:
                    txt = "Too complex function, complex function in {} Contract: {}, Function: {}"
                if issue.type == Complex.HIGH_STATE_VARIABLES:
                    pass

                info = txt.format(self.filename,
                                    c.name,
                                    func_name)

                
                    txt = "Too many "
                    info = txt.format(self.filename,
                                    c.name,
                                    func_name)

                    self.log(info)

                    results.append({'vuln': 'SuicidalFunc',
                                    'sourceMapping': func.source_mapping,
                                    'filename': self.filename,
                                    'contract': c.name,
                                    'func': func_name})

        return result

