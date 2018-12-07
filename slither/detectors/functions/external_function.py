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

    WIKI = 'https://github.com/trailofbits/slither/wiki/Vulnerabilities-Description#public-function-that-could-be-declared-as-external'

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
        all_info = ''

        for contract in self.slither.contracts_derived:
            if self._contains_internal_dynamic_call(contract):
                continue

            func_list = self.detect_functions_called(contract)
            public_function_calls.extend(func_list)

            for func in [f for f in contract.functions if f.visibility == 'public' and\
                                                           not f in public_function_calls and\
                                                           not f.is_constructor]:
                txt = "{}.{} ({}) should be declared external\n"
                info = txt.format(func.contract.name,
                                  func.name,
                                  func.source_mapping_str)
                all_info += info

                json = self.generate_json_result()
                self.add_function_to_json(func, json)
                results.append(json)
        if all_info != '':
            self.log(all_info)
        return results
