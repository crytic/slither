"""

    # TODO: Add in other CK metrics (NOC, DIT)
    # TODO: Don't display all the general function metrics, but add those to complexity-dashboard
    CK Metrics are a suite of six software metrics proposed by Chidamber and Kemerer in 1994.
    These metrics are used to measure the complexity of a class.
    https://en.wikipedia.org/wiki/Programming_complexity

    - Response For a Class (RFC) is a metric that measures the number of unique method calls within a class.
    - Number of Children (NOC) is a metric that measures the number of children a class has.
    - Depth of Inheritance Tree (DIT) is a metric that measures the number of parent classes a class has.

    Not implemented:
    - Lack of Cohesion of Methods (LCOM) is a metric that measures the lack of cohesion in methods.
    - Weighted Methods per Class (WMC) is a metric that measures the complexity of a class.
    - Coupling Between Object Classes (CBO) is a metric that measures the number of classes a class is coupled to.

"""
from typing import Tuple
from slither.printers.abstract_printer import AbstractPrinter
from slither.utils.myprettytable import make_pretty_table
from slither.slithir.operations.high_level_call import HighLevelCall
from slither.utils.colors import bold


def compute_dit(contract, depth=0):
    """
    Recursively compute the depth of inheritance tree (DIT) of a contract
    Args:
        contract: Contract - the contract to compute the DIT for
        depth: int - the depth of the contract in the inheritance tree
    Returns:
        the depth of the contract in the inheritance tree
    """
    if not contract.inheritance:
        return depth
    max_dit = depth
    for inherited_contract in contract.inheritance:
        dit = compute_dit(inherited_contract, depth + 1)
        max_dit = max(max_dit, dit)
    return max_dit


# pylint: disable=too-many-locals
def compute_metrics(contracts):
    """
    Compute CK metrics of a contract
    Args:
        contracts(list): list of contracts
    Returns:
        a tuple of (metrics1, metrics2, metrics3, metrics4, metrics5)
        # Visbility
        metrics1["contract name"] = {
            "State variables":int,
            "Constants":int,
            "Immutables":int,
        }
        metrics2["contract name"] = {
            "Public": int,
            "External":int,
            "Internal":int,
            "Private":int,
        }
        # Mutability
        metrics3["contract name"] = {
            "Mutating":int,
            "View":int,
            "Pure":int,
        }
        # External facing, mutating: total / no auth / no modifiers
        metrics4["contract name"] = {
            "External mutating":int,
            "No auth or onlyOwner":int,
            "No modifiers":int,
        }
        metrics5["contract name"] = {
            "Ext calls":int,
            "Response For a Class":int,
            "NOC":int,
            "DIT":int,
        }

        RFC is counted as follows:
        +1 for each public or external fn
        +1 for each public getter
        +1 for each UNIQUE external call

    """
    metrics1 = {}
    metrics2 = {}
    metrics3 = {}
    metrics4 = {}
    metrics5 = {}
    dependents = {
        inherited.name: {
            contract.name for contract in contracts if inherited.name in contract.inheritance
        }
        for inherited in contracts
    }

    for c in contracts:
        (state_variables, constants, immutables, public_getters) = count_variables(c)
        rfc = public_getters  # add 1 for each public getter
        metrics1[c.name] = {
            "State variables": state_variables,
            "Constants": constants,
            "Immutables": immutables,
        }
        metrics2[c.name] = {
            "Public": 0,
            "External": 0,
            "Internal": 0,
            "Private": 0,
        }
        metrics3[c.name] = {
            "Mutating": 0,
            "View": 0,
            "Pure": 0,
        }
        metrics4[c.name] = {
            "External mutating": 0,
            "No auth or onlyOwner": 0,
            "No modifiers": 0,
        }
        metrics5[c.name] = {
            "Ext calls": 0,
            "RFC": 0,
            "NOC": len(dependents[c.name]),
            "DIT": compute_dit(c),
        }
        for func in c.functions:
            if func.name == "constructor":
                continue
            pure = func.pure
            view = not pure and func.view
            mutating = not pure and not view
            external = func.visibility == "external"
            public = func.visibility == "public"
            internal = func.visibility == "internal"
            private = func.visibility == "private"
            external_public_mutating = external or public and mutating
            external_no_auth = external_public_mutating and no_auth(func)
            external_no_modifiers = external_public_mutating and len(func.modifiers) == 0
            if external or public:
                rfc += 1

            high_level_calls = [
                ir for node in func.nodes for ir in node.irs_ssa if isinstance(ir, HighLevelCall)
            ]

            # convert irs to string with target function and contract name
            external_calls = []
            for h in high_level_calls:
                if hasattr(h.destination, "name"):
                    external_calls.append(f"{h.function_name}{h.destination.name}")
                else:
                    external_calls.append(f"{h.function_name}{h.destination.type.type.name}")

            rfc += len(set(external_calls))

            metrics2[c.name]["Public"] += 1 if public else 0
            metrics2[c.name]["External"] += 1 if external else 0
            metrics2[c.name]["Internal"] += 1 if internal else 0
            metrics2[c.name]["Private"] += 1 if private else 0

            metrics3[c.name]["Mutating"] += 1 if mutating else 0
            metrics3[c.name]["View"] += 1 if view else 0
            metrics3[c.name]["Pure"] += 1 if pure else 0

            metrics4[c.name]["External mutating"] += 1 if external_public_mutating else 0
            metrics4[c.name]["No auth or onlyOwner"] += 1 if external_no_auth else 0
            metrics4[c.name]["No modifiers"] += 1 if external_no_modifiers else 0

            metrics5[c.name]["Ext calls"] += len(external_calls)
            metrics5[c.name]["RFC"] = rfc

    return metrics1, metrics2, metrics3, metrics4, metrics5


def count_variables(contract) -> Tuple[int, int, int, int]:
    """Count the number of variables in a contract
    Args:
        contract(core.declarations.contract.Contract): contract to count variables
    Returns:
        Tuple of (state_variable_count, constant_count, immutable_count, public_getter)
    """
    state_variable_count = 0
    constant_count = 0
    immutable_count = 0
    public_getter = 0
    for var in contract.variables:
        if var.is_constant:
            constant_count += 1
        elif var.is_immutable:
            immutable_count += 1
        else:
            state_variable_count += 1
        if var.visibility == "Public":
            public_getter += 1
    return (state_variable_count, constant_count, immutable_count, public_getter)


def no_auth(func) -> bool:
    """
    Check if a function has no auth or only_owner modifiers
    Args:
        func(core.declarations.function.Function): function to check
    Returns:
        bool
    """
    for modifier in func.modifiers:
        if "auth" in modifier.name or "only_owner" in modifier.name:
            return False
    return True


class CKMetrics(AbstractPrinter):
    ARGUMENT = "ck"
    HELP = "Computes the CK complexity metrics for each contract"

    WIKI = "https://github.com/trailofbits/slither/wiki/Printer-documentation#ck"

    def output(self, _filename):
        if len(self.contracts) == 0:
            return self.generate_output("No contract found")
        metrics1, metrics2, metrics3, metrics4, metrics5 = compute_metrics(self.contracts)
        txt = bold("\nCK complexity metrics\n")
        # metrics2: variable counts
        txt += bold("\nVariables\n")
        keys = list(metrics1[self.contracts[0].name].keys())
        table0 = make_pretty_table(["Contract", *keys], metrics1, True)
        txt += str(table0) + "\n"

        # metrics3: function visibility
        txt += bold("\nFunction visibility\n")
        keys = list(metrics2[self.contracts[0].name].keys())
        table1 = make_pretty_table(["Contract", *keys], metrics2, True)
        txt += str(table1) + "\n"

        # metrics4: function mutability counts
        txt += bold("\nFunction mutatability\n")
        keys = list(metrics3[self.contracts[0].name].keys())
        table2 = make_pretty_table(["Contract", *keys], metrics3, True)
        txt += str(table2) + "\n"

        # metrics5: external facing mutating functions
        txt += bold("\nExternal/Public functions with modifiers\n")
        keys = list(metrics4[self.contracts[0].name].keys())
        table3 = make_pretty_table(["Contract", *keys], metrics4, True)
        txt += str(table3) + "\n"

        # metrics5: ext calls and rfc
        txt += bold("\nExt calls and RFC\n")
        keys = list(metrics5[self.contracts[0].name].keys())
        table4 = make_pretty_table(["Contract", *keys], metrics5, False)
        txt += str(table4) + "\n"

        res = self.generate_output(txt)
        res.add_pretty_table(table0, "CK complexity core metrics 1/5")
        res.add_pretty_table(table1, "CK complexity core metrics 2/5")
        res.add_pretty_table(table2, "CK complexity core metrics 3/5")
        res.add_pretty_table(table3, "CK complexity core metrics 4/5")
        res.add_pretty_table(table4, "CK complexity core metrics 5/5")
        self.info(txt)

        return res
