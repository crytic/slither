from slither.detectors.abstract_detector import AbstractDetector, DetectorClassification
from collections import defaultdict
from slither.slithir.operations import Delete, Index, TypeConversion
from slither.detectors.arithmetic.temp_and_reference_variables import Handle_TmpandRefer

class DeleteDynamicArrayElement(AbstractDetector):
    """
    Documentation
    """

    ARGUMENT = 't1' # slither will launch the detector with slither.py --detect mydetector
    HELP = 'Help printed by slither'
    IMPACT = DetectorClassification.HIGH
    CONFIDENCE = DetectorClassification.HIGH

    WIKI = ''

    WIKI_TITLE = ''
    WIKI_DESCRIPTION = ''
    WIKI_EXPLOIT_SCENARIO = ''
    WIKI_RECOMMENDATION = ''

    def detect_incorrect_delete(func):
        tmp = Handle_TmpandRefer()
        del_elements = []
        res = []

        for node in func.nodes:
            for ir in node.irs:
                temp_vars = tmp.temp

                if isinstance(ir, Delete):
                    del_elements.append(node)

                if isinstance(ir, Index):
                    tmp.handle_index(ir)

                if isinstance(ir, TypeConversion):
                    tmp.handle_conversion(ir)
                
                

        return res

    def _detect(self):
        for contract in self.contracts:
            for function in contract.functions_declared:
                result = self.detect_incorrect_delete(function)
                


                if result:
                    info = ['This is an example']
                    res = self.generate_result(info)

        return [res]