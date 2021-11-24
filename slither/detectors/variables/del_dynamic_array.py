from collections import defaultdict
from slither.detectors.abstract_detector import AbstractDetector, DetectorClassification
from slither.detectors.arithmetic.temp_and_reference_variables import  Handle_TmpandRefer
from slither.slithir.operations import Delete, Index, Length, TypeConversion, Binary, BinaryType
from slither.slithir.operations.length import Length
from slither.slithir.variables import ReferenceVariable, TemporaryVariable, Constant

class DeleteDynamicArrayElement(AbstractDetector):
    ARGUMENT = "delete-array"
    HELP = "Array element dosnt delete clearly"
    IMPACT = DetectorClassification.INFORMATIONAL
    CONFIDENCE = DetectorClassification.HIGH

    WIKI = "https://github.com/crytic/slither/wiki/Detector-Documentation/#delete-array"

    WIKI_TITLE = "Delete Dynamic Array Element"
    WIKI_DESCRIPTION = "In Solidity, deleting dynamic array elements does not automatically shorten the length of the array and move the array elements. You need to manually shorten the array length and manually shift the elements. Otherwise, gaps are left in the array (the deleted element is simply set as the default)."

    # region wiki_exploit_scenario
    WIKI_EXPLOIT_SCENARIO = """
```solidity
//from JiuZhou

function deletePartner(address _badGuy) external onlyOwner{
        uint256 _length = myPartners.length;
        for(uint256 i = 0; i < _length; i++){
            if(myPartners[i] == _badGuy)
                delete myPartners[i];
        }
    }
```
"""
    # endregion wiki_exploit_scenario

    WIKI_RECOMMENDATION = "Manually modify the array length and shift the elements"

    def detect_incorrect_delete(self,func):
        tmp = Handle_TmpandRefer()
        del_elements = defaultdict(list)
        res = []
        
        for node in func.nodes:
        
            for ir in node.irs:
                temp_vars = tmp.temp

                if isinstance(ir, Index):
                    tmp.handle_index(ir)

                elif isinstance(ir, TypeConversion):
                    tmp.handle_conversion(ir)

                elif isinstance(ir, Length):
                    tmp.handle_length(ir)

                elif isinstance(ir, Delete):
                    if "pop()" in str(node.expression):
                        continue

                    var = ir.variable
                    if isinstance(var, (ReferenceVariable, TemporaryVariable)) and (var in temp_vars):
                        var = temp_vars[ir.variable][0]
                    del_elements[var].append(node)

                elif isinstance(ir, Binary) and ir.type == BinaryType.SUBTRACTION:
                    l = ir.variable_left
                    if isinstance(l , Constant):
                        continue
                    if l in tmp.length:
                        l = temp_vars[l][0]
                        
                        if l in del_elements:
                            del_elements.pop(l)

        for key in del_elements:
            res.append(del_elements[key][0])
                

        return res

    def _detect(self):
        results = []
        for contract in self.contracts:
            for function in contract.functions_declared:
                bugs = self.detect_incorrect_delete(function)

                for bug in bugs:
                    info = [bug, " dosn't delete array element clearly.\n",]

                    res = self.generate_result(info)
                    results.append(res)

        return results
