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
        """ Returns a list of InternallCall, InternalDynamicCall, SolidityCall, HighLevelCall
            calls made in a function

        Returns:
            (list): List of all InternallCall, InternalDynamicCall, SolidityCall, HighLevelCall
        """
        result = []
        for node in func.nodes:
            for ir in node.irs:
                if isinstance(ir, ( InternalCall, InternalDynamicCall, HighLevelCall, SolidityCall )):
                    result.append(ir.function)
        return result

    def detect_external(self, contract):
        ret = []
        for f in [f for f in contract.functions if f.contract == contract]:
            calls = self.detect_function_calls(f)
            ret.extend(calls)
        return ret

    def detect(self):
        results = []

        public_function_calls = []
        for contract in self.slither.contracts_derived:
            """
            Returns list of InternallCall, InternalDynamicCall, HighLevelCall, SolidityCall calls
            in contract functions
            """
            func_list = self.detect_external(contract)
            # appends the list to public function calls
            public_function_calls.extend(func_list)

        for c in self.contracts:
            """
            Returns a list of functions with public visibility in contract that doesn't
            exist in the public_function_calls_list

            This means that the public function doesn't have any
            InternallCall, InternalDynamicCall, SolidityCall call
            attached to it hence it can be declared as external

            """
            functions = [ f for f in c.functions if f.visibility == "public"
                         and
                         f.contract == c
                         and
                         f not in public_function_calls ]

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