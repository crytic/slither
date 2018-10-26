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
    HELP = 'Detect public function that could be declared as external'
    IMPACT = DetectorClassification.INFORMATIONAL
    CONFIDENCE = DetectorClassification.HIGH

    @staticmethod
    def detect_function_calls(func):
        """ Returns a list of InternallCall, InternalDynamicCall, SolidityCall
            calls made in a function

        Returns:
            (list): List of all InternallCall, InternalDynamicCall, SolidityCall
        """
        result = []
        containsInternalDynamicCall = False
        for node in func.nodes:
            for ir in node.irs:
                if isinstance(ir, (InternalDynamicCall)):
                    containsInternalDynamicCall = True
                    break
                if isinstance(ir, (InternalCall, SolidityCall)):
                    result.append(ir.function)
        return result, containsInternalDynamicCall

    def detect_public(self, contract):
        ret = []
        containsInternalDynamicCall = False
        for f in contract.all_functions_called:
            calls, containsInternalDynamicCall = self.detect_function_calls(f)
            if containsInternalDynamicCall:
                break
            else:  
                ret.extend(calls)
        return ret, containsInternalDynamicCall

    def detect(self):
        results = []

        public_function_calls = []

        """ Exclude contracts with InternalDynamicCall
        """
        excluded_contracts = []

        for contract in self.slither.contracts_derived:
            """
            Returns list of InternallCall, InternalDynamicCall, HighLevelCall, SolidityCall calls
            in contract functions
            """
            func_list, exclude_contract = self.detect_public(contract)

            if exclude_contract:
                excluded_contracts.append(contract)
            else:
                # appends the list to public function calls
                public_function_calls.extend(func_list)
                
        for c in [ contract for contract in self.contracts if contract not in excluded_contracts ]:
            """
            Returns a list of functions with public visibility in contract that doesn't
            exist in the public_function_calls

            This means that the public function doesn't have any
            InternallCall, InternalDynamicCall, SolidityCall call
            attached to it hence it can be declared as external

            """
            functions = [ func for func in c.functions if func.visibility == "public"
                         and
                         func.contract == c
                         and
                         func not in public_function_calls ]

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