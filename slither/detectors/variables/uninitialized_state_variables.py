"""
    Module detecting state uninitialized variables
    Recursively check the called functions

    The heuristic checks:
    - state variables including mappings/refs
    - LibraryCalls, InternalCalls, InternalDynamicCalls with storage variables

    Only analyze "leaf" contracts (contracts that are not inherited by another contract)
"""

from slither.detectors.abstract_detector import AbstractDetector, DetectorClassification
from slither.core.variables.state_variable import StateVariable
from slither.slithir.variables import ReferenceVariable
from slither.slithir.operations.assignment import Assignment

from slither.slithir.operations import (OperationWithLValue, Index, Member,
                                        InternalCall, InternalDynamicCall, LibraryCall)


class UninitializedStateVarsDetection(AbstractDetector):
    """
    Constant function detector
    """

    ARGUMENT = 'uninitialized-state'
    HELP = 'Uninitialized state variables'
    IMPACT = DetectorClassification.HIGH
    CONFIDENCE = DetectorClassification.HIGH

    @staticmethod
    def written_variables(contract):
        ret = []
        for f in contract.all_functions_called + contract.modifiers:
            for n in f.nodes:
                for ir in n.irs:
                    if isinstance(ir, (Index, Member)):
                        continue  # Don't consider Member and Index operations -> ReferenceVariable
                    elif isinstance(ir, OperationWithLValue) and isinstance(ir.lvalue, StateVariable):
                        ret.append(ir.lvalue)
                    elif isinstance(ir, Assignment) and isinstance(ir.lvalue, ReferenceVariable):
                        dest = ir.lvalue
                        while isinstance(dest, ReferenceVariable):
                            dest = dest.points_to
                        ret.append(dest)
                    elif isinstance(ir, LibraryCall) \
                            or isinstance(ir, InternalCall) \
                            or isinstance(ir, InternalDynamicCall):
                        for v in ir.arguments:
                            ret.append(v)
                        for param in f.parameters:
                            if param.location == 'storage':
                                ret.append(param)

        return ret

    def detect_uninitialized(self, contract):
        written_variables = self.written_variables(contract)
        return [(variable, contract.get_functions_reading_from_variable(variable))
                for variable in contract.state_variables if variable not in written_variables]

    def detect(self):
        """ Detect uninitialized state variables

        Recursively visit the calls
        Returns:
            dict: [contract name] = set(state variable uninitialized)
        """
        results = []
        for c in self.slither.contracts_derived:
            ret = self.detect_uninitialized(c)
            for variable, functions in ret:
                info = "Uninitialized state variable in %s, " % self.filename + \
                       "Contract: %s, Variable: %s, Used in %s" % (c.name,
                                                                   str(variable),
                                                                   [str(f) for f in functions])
                self.log(info)

                source = [variable.source_mapping]
                source += [f.source_mapping for f in functions]

                results.append({'vuln': 'UninitializedStateVars',
                                'sourceMapping': source,
                                'filename': self.filename,
                                'contract': c.name,
                                'functions': [str(f) for f in functions],
                                'variable': str(variable)})

        return results
