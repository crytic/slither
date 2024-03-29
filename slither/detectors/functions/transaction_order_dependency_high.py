import itertools
from typing import List

from slither.core.declarations.function_contract import FunctionContract
from slither.core.variables.state_variable import StateVariable
from slither.detectors.abstract_detector import AbstractDetector, DetectorClassification
from slither.utils.function_dependency_tree import build_dependency_tree_token_flow_or_money_flow
from slither.utils.function_permission_check import function_has_caller_check, function_can_only_initialized_once
from slither.detectors.functions.modifier_utils import ModifierUtil


class TransactionOrderDependencyHigh(AbstractDetector):  # pylint: disable=too-few-public-methods
    """
    Documentation
    """

    ARGUMENT = "transaction-order-dependency-high"  # falcon will launch the detector with slither.py --mydetector
    HELP = "check race conditions among contract functions (namely transaction order dependency)"
    IMPACT = DetectorClassification.CRITICAL
    CONFIDENCE = DetectorClassification.HIGH

    WIKI = """https://swcregistry.io/docs/SWC-114"""

    WIKI_TITLE = "transaction order dependency relevant to money flow or token flow"
    WIKI_DESCRIPTION = "transaction-order-dependency plugin"
    WIKI_EXPLOIT_SCENARIO = ".."
    WIKI_RECOMMENDATION = ".."
    ERC20_FUNCTION = [
    "transferFrom",
    "safeTransferFrom",
    "mint",
    "burn",
    "burnFrom",
    "approve",
    "balanceOf",
    "totalSupply",
    "transfer",
    "allowance",
    "safeTransfer",
    "safeApprove",
    "getReserve",
    "transfer",
    "balance"
]
    def analyzeTOD(self, fns: List[FunctionContract]):
        results = []

        def analyzePairFunction(fn1: FunctionContract, fn2: FunctionContract):
            if function_has_caller_check(fn1) and function_has_caller_check(fn2):
                return False, []
            if fn1.canonical_name in self.money_flow_strong_dependency_tree:
                if fn2 in self.money_flow_strong_dependency_tree[fn1.canonical_name]:
                    return True, set(fn1.all_state_variables_read()).intersection(
                        set(fn2.all_state_variables_written()))

            if fn2.canonical_name in self.money_flow_strong_dependency_tree:
                if fn1 in self.money_flow_strong_dependency_tree[fn2.canonical_name]:
                    return True, set(fn2.all_state_variables_read()).intersection(
                        set(fn1.all_state_variables_written()))

            return False, []

        for com in itertools.combinations(range(len(fns)), 2):
            check, vars = analyzePairFunction(fns[com[0]], fns[com[1]])
            if check:
                results.append([fns[com[0]], fns[com[1]], vars])
        return results

    def _detect(self):
        results = []
        for contract in self.contracts:
            if not contract.is_interface:
                permissionless_functions = list()
                for fn in contract.functions:
                    if ModifierUtil._has_msg_sender_check_new(fn) or len(fn.modifiers) > 0 or fn.visibility in ["private", "internal"]:
                        continue
                    if fn.view or fn.pure or fn.is_fallback or \
                            fn.is_constructor or fn.is_constructor_variables or "init" in fn.name or "set" in fn.name \
                            or len(fn.modifiers)>0 or any(ERC20_NAME in fn.name for ERC20_NAME in self.ERC20_FUNCTION)\
                            or len(fn.state_variables_written) <= 0:
                        continue
                    if not function_can_only_initialized_once(fn):
                        permissionless_functions.append(fn)
                if len(permissionless_functions) <= 1:
                    continue
                self.money_flow_weak_dependency_tree, self.money_flow_strong_dependency_tree = build_dependency_tree_token_flow_or_money_flow(
                    contract)
                todresults = self.analyzeTOD(fns=permissionless_functions)
                for tod in todresults:
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
