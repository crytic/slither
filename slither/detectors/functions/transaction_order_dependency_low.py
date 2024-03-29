import itertools
from typing import List
from slither.utils.function_dependency_tree import build_dependency_tree
from slither.core.declarations.function_contract import FunctionContract
from slither.detectors.abstract_detector import AbstractDetector, DetectorClassification
from slither.core.variables.state_variable import StateVariable
from slither.utils.function_permission_check import function_can_only_initialized_once, function_has_caller_check
from slither.detectors.functions.modifier_utils import ModifierUtil


class TransactionOrderDependencyLow(AbstractDetector):  # pylint: disable=too-few-public-methods
    """
    Documentation
    """

    ARGUMENT = "transaction-order-dependency-low"  # falcon will launch the detector with slither.py --mydetector
    HELP = "check race conditions among contract functions (namely transaction order dependency)"
    IMPACT = DetectorClassification.LOW
    CONFIDENCE = DetectorClassification.MEDIUM

    WIKI = """https://swcregistry.io/docs/SWC-114"""

    WIKI_TITLE = "transaction order dependency (low risk)"
    WIKI_DESCRIPTION = "transaction-order-dependency plugin"
    WIKI_EXPLOIT_SCENARIO = ".."
    WIKI_RECOMMENDATION = ".."

    def analyzeTOD(self, fns: List[FunctionContract]):
        results = []

        def analyzePairFunction(fn1: FunctionContract, fn2: FunctionContract):
            if fn1.canonical_name in self.weak_dependency_tree:
                if fn2 in self.weak_dependency_tree[fn1.canonical_name]:
                    return True, set(fn1.all_state_variables_read()).intersection(
                        set(fn2.all_state_variables_written()))

            if fn2.canonical_name in self.weak_dependency_tree:
                if fn1 in self.weak_dependency_tree[fn2.canonical_name]:
                    return True, set(fn2.all_state_variables_read()).intersection(
                        set(fn1.all_state_variables_written()))
            return False, []

        for com in itertools.combinations(range(len(fns)), 2):
            check, vars = analyzePairFunction(fns[com[0]], fns[com[1]])
            if check:
                results.append([fns[com[0]], fns[com[1]], vars])
        return results

    def _detect(self):

        info = "transaction order dependency detector"
        results = []
        for contract in self.contracts:
            if not contract.is_interface:
                permissionless_functions = list()
                for fn in contract.functions:
                    if ModifierUtil._has_msg_sender_check_new(fn) or len(fn.modifiers) > 0 or fn.visibility in ["private", "internal"]:
                        continue
                    if fn.view or fn.pure or fn.is_fallback \
                            or len(fn.state_variables_written) <= 0 \
                            or fn.is_constructor or fn.is_constructor_variables \
                            or function_has_caller_check(fn) or function_can_only_initialized_once(fn):
                        continue
                    permissionless_functions.append(fn)

                if len(permissionless_functions) <= 1:
                    continue
                self.weak_dependency_tree, self.strong_dependency_tree = build_dependency_tree(contract)
                tod_results = self.analyzeTOD(fns=permissionless_functions)

                for tod in tod_results:
                    fn1: FunctionContract = tod[0]
                    fn2: FunctionContract = tod[1]
                    _vars: List[StateVariable] = tod[2]
                    info = [fn1.full_name, " and ", fn2.full_name,
                            " have transaction order dependency caused by data race on state variables:",
                            ", ".join([_var.canonical_name for _var in _vars]), "\n"]
                    info += ["\t- ", fn1, "\n"]
                    info += ["\t- ", fn2, "\n"]
                    res = self.generate_result(info)
                    results.append(res)
        return results
