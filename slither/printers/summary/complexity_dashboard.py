"""
    Complexity dashboard
"""
from slither.printers.abstract_printer import AbstractPrinter
from slither.utils.myprettytable import make_pretty_table, make_pretty_table_simple, transpose
from slither.printers.summary.halstead import compute_halstead
from slither.printers.summary.martin import compute_coupling
from slither.printers.summary.loc import compute_loc_metrics
from slither.printers.summary.ck import compute_ck_metrics
from slither.utils.code_complexity import compute_cyclomatic_complexity, count_abstracts

def make_cyclomatic_complexity_table(contracts, with_functions=False):
    ret = {}
    for contract in contracts:
        ret[contract.name] = {"Cyclomatic complexity": 0}
        for function in contract.functions:
            complexity = compute_cyclomatic_complexity(function)
            if with_functions:
                ret[contract.name][function.name] = {"Cyclomatic complexity": complexity}
            else:
                ret[contract.name]["Cyclomatic complexity"] += complexity
    return ret

class ComplexityDashboard(AbstractPrinter):
    ARGUMENT = "complexity-dashboard"
    HELP = "Combines all complexity metrics into one printer"

    WIKI = "https://github.com/trailofbits/slither/wiki/Printer-documentation#complexity-dashboard"

    def output(self, _filename):
        non_interface_contracts = [contract for contract in self.contracts if not contract.is_interface]
        if len(non_interface_contracts) == 0:
            return self.generate_output("No contract found")
        txt = "\n\nComplexity dashboard\n\n"
        tables = []

        # LOC
        txt += "\nLines of code:\n"
        lines_dict = compute_loc_metrics(self.slither).to_dict()
        headers = [""] + list(lines_dict.keys())
        report_dict = transpose(lines_dict)
        table = make_pretty_table(headers, report_dict)
        txt += str(table) + "\n"
        tables += [(table, "Lines of code")]

        # Function attributes (From CK printer)
        metrics1, metrics2, metrics3, metrics4, metrics5 = compute_ck_metrics(non_interface_contracts)
        # metrics1: variable counts
        txt += "\nVariables\n"
        keys = list(metrics1[non_interface_contracts[0].name].keys())
        table = make_pretty_table(["Contract", *keys], metrics1, True)
        txt += str(table) + "\n"
        tables += [(table, "CK complexity metrics1")]

        # metrics2: function visibility
        txt += "\nFunction visibility\n"
        keys = list(metrics2[non_interface_contracts[0].name].keys())
        table = make_pretty_table(["Contract", *keys], metrics2, True)
        txt += str(table) + "\n"
        tables += [(table, "CK complexity metrics2")]

        # metrics3: function mutability counts
        txt += "\nState mutability\n"
        keys = list(metrics3[non_interface_contracts[0].name].keys())
        table = make_pretty_table(["Contract", *keys], metrics3, True)
        txt += str(table) + "\n"
        tables += [(table, "CK complexity metrics3")]

        # metrics4: external facing mutating functions
        txt += "\nExternal/Public functions with modifiers\n"
        keys = list(metrics4[non_interface_contracts[0].name].keys())
        table = make_pretty_table(["Contract", *keys], metrics4, True)
        txt += str(table) + "\n"
        tables += [(table, "CK complexity metrics4")]

        # Cyclomatic complexity
        txt += "\nCyclomatic complexity:\n"
        cyclomatic_complexity_dict = make_cyclomatic_complexity_table(non_interface_contracts)
        table = make_pretty_table(["Contract", "Cyclomatic complexity"], cyclomatic_complexity_dict, True)
        txt += str(table) + "\n"
        tables += [(table, "Cyclomatic complexity")]

        # Martin agile software metrics (Ca, Ce, I, A, D)
        (abstract_contract_count, total_contract_count) = count_abstracts(non_interface_contracts)
        abstractness = float(abstract_contract_count / total_contract_count)

        txt += "\nMartin agile software metrics:\n"
        coupling_dict = compute_coupling(non_interface_contracts, abstractness)

        table = make_pretty_table(
            ["Contract", *list(coupling_dict[non_interface_contracts[0].name].keys())], coupling_dict
        )
        txt += str(table) + "\n"
        tables += [(table, "Martin agile software metrics")]

        # Halstead - Core metrics: operations and operands
        core, extended1, extended2 = compute_halstead(non_interface_contracts)
        txt += "\nHalstead complexity core metrics:\n"
        keys = [k for k in core[non_interface_contracts[0].name].keys()]
        table = make_pretty_table(["Contract", *keys], core, False)
        txt += str(table) + "\n"
        tables += [(table, "Halstead core metrics")]

        # Halstead - Extended metrics1: vocabulary, program length, estimated length, volume
        txt += "\nHalstead complexity extended metrics1:\n"
        keys = list(extended1[non_interface_contracts[0].name].keys())
        table = make_pretty_table(["Contract", *keys], extended1, False)
        txt += str(table) + "\n"
        tables += [(table, "Halstead extended metrics1")]

        # Halstead - Extended metrics2: difficulty, effort, time, bugs
        txt += "\nHalstead complexity extended metrics2:\n"
        keys = list(extended2[non_interface_contracts[0].name].keys())
        table = make_pretty_table(["Contract", *keys], extended2, False)
        txt += str(table) + "\n"
        tables += [(table, "Halstead extended metrics2")]

        # CK Metrics
        txt += "\nExternal calls and CK Metrics:\n"
        keys = list(metrics5[non_interface_contracts[0].name].keys())
        table = make_pretty_table(["Contract", *keys], metrics5, False)
        txt += str(table) + "\n"
        tables += [(table, "CK complexity metrics5")]

        # Project wide metrics

        # Create a dict of project wide metrics for display in a table
        # { "metric": <value>, ... }
        project_metrics = {}  # TODO: would be nice to have columns "overall", "contract min", "contract max", "contract avg"

        total_functions = sum([len(contract.functions) for contract in non_interface_contracts])
        project_metrics["SLOC (in src files)"] = lines_dict["src"]["sloc"]
        project_metrics["Number of contracts"] = total_contract_count
        project_metrics["Number of functions"] = total_functions
        external_fns = sum([metrics2[contract.name]["External"] for contract in non_interface_contracts]) + sum([metrics2[contract.name]["Public"] for contract in non_interface_contracts])
        project_metrics["Number of public/external functions"] = external_fns
        external_mutating = sum([metrics4[contract.name]["External mutating"] for contract in non_interface_contracts])
        project_metrics["Number of external, mutating functions"] = external_mutating
        external_mutating_noauth = sum([metrics4[contract.name]["No auth or onlyOwner"] for contract in non_interface_contracts])
        project_metrics["Number of external, mutating functions -- no auth"] = external_mutating_noauth

        project_metrics["Number of abstract contracts"] = abstract_contract_count
        project_metrics["Abstractness (A)"] = f"{abstractness:.3f}"
        project_metrics["Average cyclomatic complexity"] = sum([cyclomatic_complexity_dict[contract.name]["Cyclomatic complexity"] for contract in non_interface_contracts if not contract.is_interface])
        totals_key = "ALL CONTRACTS" if len(non_interface_contracts) > 1 else non_interface_contracts[0].name
        average_halstead_volume = int(float(extended1[totals_key]["Volume"]) / len(non_interface_contracts))
        project_metrics["Average Halstead volume"] = average_halstead_volume

        table = make_pretty_table_simple(project_metrics, "Project metrics")
        txt += str(table) + "\n"
        tables += [(table, "Project metrics")]


        self.info(txt)
        res = self.generate_output(txt)
        for (table, title) in tables:
            res.add_pretty_table(table, title)
        return res
