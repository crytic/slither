from slither.detectors.abstract_detector import (AbstractDetector,
                                                 DetectorClassification)
from slither.slithir.operations import (HighLevelCall, SolidityCall )
from slither.slithir.operations import (InternalCall, InternalDynamicCall)

class ExternalFunction(AbstractDetector):
    """
    Detect public function that could be declared as external
    """

    ARGUMENT = 'external-function'
    HELP = 'Detect public function that could be declared as external'
    IMPACT = DetectorClassification.INFORMATIONAL
    CONFIDENCE = DetectorClassification.HIGH

    @staticmethod
    def detect_function_calls(func):
        """ Returns a list of all InternallCall, InternalDynamicCall, SolidityCall
            calls made in a function

        Returns:
            (list): List of all InternallCall, InternalDynamicCall, SolidityCall
        """
        result = []
        for node in func.nodes:
            for ir in node.irs:
                if isinstance(ir, ( InternalCall, InternalDynamicCall, HighLevelCall, SolidityCall )):
                    print(ir.function)
                    result.append(ir.function)
        return result

    def detect_external(self, contract):
        ret = []
        for f in [f for f in contract.functions if f.contract == contract]:
            calls = self.detect_function_calls(f)
            ret = [ret.append(f) for f in calls]
        return ret

    def detect(self):
        results = []

        public_function_calls = []
        for contract in self.slither.contracts_derived:
            # get the contract functions
            func_list = self.detect_external(contract)
            public_function_calls = [public_function_calls.append(f) for f in func_list]

        print(public_function_calls_list)

        for c in self.contracts:
            """
            Returns the list of functions with public visibility in contract doesn't exist in the public_function_calls_list
            This means that the public function doesn't have any InternallCall, InternalDynamicCall, SolidityCall call
            attached to it hence 
            """
            functions = [f for f in c.functions if f.visibility == "public" and f.contract == c and f not in public_function_calls_list]

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