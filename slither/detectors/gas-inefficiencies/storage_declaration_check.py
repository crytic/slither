from slither.detectors.abstract_detector import AbstractDetector, DetectorClassification, Issue
from slither.core.solidity_types.user_defined_type import UserDefinedType
from slither.analyses.data_dependency.data_dependency import DataDependency
from slither.slithir.operations import MemberAccess, ArrayAccess
from slither.core.declarations import ContractVariable
from slither.slithir.operations import For, While


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

    def _evaluate(self):
        # Get all user-defined types
        user_defined_types = [x for x in self.contract.variables if isinstance(x.type, UserDefinedType)]

        # Loop through each user-defined type
        for udt in user_defined_types:
            # Get all MemberAccess and ArrayAccess nodes that reference this user-defined type
            data_dependency = DataDependency(self.contract)
            dependent_nodes = data_dependency.get_dependent_nodes(udt.name)

            # Check if any of the dependent nodes are inside a loop
            for node in dependent_nodes:
                parent_node = node.parent
                while parent_node:
                    if isinstance(parent_node, (For, While)):
                        self._issues.append(
                            Issue(
                                node,
                                "Consider using a storage variable instead of repeatedly fetching the reference in a map or an array.",
                                self,
                                confidence=DetectorClassification.MEDIUM,
                            )
                        )
                        break
                    parent_node = parent_node.parent
