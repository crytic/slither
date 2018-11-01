from slither.detectors.abstract_detector import (AbstractDetector,
                                                 DetectorClassification)
from slither.slithir.operations import (HighLevelCall, SolidityCall )
from slither.slithir.operations import (InternalCall, InternalDynamicCall)

class ExternalFunction(AbstractDetector):
    """
    Detect public function that could be declared as external

    IMPROVEMENT: Add InternalDynamicCall check
    https://github.com/trailofbits/slither/pull/53#issuecomment-432809950
    """

    ARGUMENT = 'external-function'
    HELP = 'Public function that could be declared as external'
    IMPACT = DetectorClassification.INFORMATIONAL
    CONFIDENCE = DetectorClassification.HIGH

    @staticmethod
    def detect_functions_called(contract):
        """ Returns a list of InternallCall, SolidityCall
            calls made in a function

        Returns:
            (list): List of all InternallCall, SolidityCall
        """
        result = []
        for func in contract.all_functions_called:
            for node in func.nodes:
                for ir in node.irs:
                    if isinstance(ir, (InternalCall, SolidityCall)):
                        result.append(ir.function)
        return result

    @staticmethod
    def _contains_internal_dynamic_call(contract):
        for func in contract.all_functions_called:
            for node in func.nodes:
                for ir in node.irs:
                    if isinstance(ir, (InternalDynamicCall)):
                        return True
        return False

    def detect(self):
        results = []

        public_function_calls = []

        for contract in sorted(self.slither.contracts_derived, key=lambda c: c.name):
            if self._contains_internal_dynamic_call(contract):
                continue

            func_list = self.detect_functions_called(contract)
            public_function_calls.extend(func_list)

            for func in [f for f in sorted(contract.functions, key=lambda x: x.name) if f.visibility == 'public' and\
                                                           not f in public_function_calls and\
                                                           not f.is_constructor]:
                func_name = func.name
                txt = "Public function in {} Contract: {}, Function: {} should be declared external"
                info = txt.format(self.filename,
                                  contract.name,
                                  func_name)
                self.log(info)
                results.append({'vuln': 'ExternalFunc',
                                'sourceMapping': func.source_mapping,
                                'filename': self.filename,
                                'contract': contract.name,
                                'func': func_name})
        return results
