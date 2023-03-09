from slither.detectors.abstract_detector import AbstractDetector, DetectorClassification
from slither.core.solidity_types.user_defined_type import UserDefinedType

class GasStorageDeclarationCheck(AbstractDetector):
    """
    Gas: It is more gas efficient to declare a storage variable and use it than to repeatedly fetch the reference in a map or array.
    """

    ARGUMENT = "storage-declaration-check"
    HELP = "You can streamline the referencing of a storage variable by declaring and using it, rather than fetching the variable repeatedly in a map or an array."
    IMPACT = DetectorClassification.OPTIMIZATION
    CONFIDENCE = DetectorClassification.MEDIUM

    WIKI = "https://github.com/demis1997/slither-gas-optimizer-detector/wiki/Solidity-Gas-Optimizations-and-Tricks#help-the-optimizer-by-saving-a-storage-variables-reference"
    WIKI_TITLE = "Help the Optimizer by Saving a Storage Variable’s Reference"
    WIKI_DESCRIPTION = "To help the optimizer, declare a storage type variable and use it instead of repeatedly fetching the reference in a map or an array. The effect can be quite significant." 

    def _detect(self):
        # Get all user-defined types
        user_defined_types = [x for x in self.contract.variables if isinstance(x.type, UserDefinedType)]

        results = []
        # Loop through each user-defined type
        for udt in user_defined_types:
            # Check if any function contains an assignment to a member of the user-defined type
            for function in self.contract.functions:
                for instruction in function.instructions:
                    if instruction.lvalue and instruction.lvalue.type == udt:
                        results.append({
                            'variable': str(instruction.lvalue),
                            'description': 'Consider using a storage variable instead of repeatedly fetching the reference in a map or an array.',
                            'severity': 'medium'
                        })
                        break
        return {'GasStorageDeclarationCheck': results}
