"""
    Complexity dashboard
"""
from slither.printers.abstract_printer import AbstractPrinter
from slither.utils.myprettytable import make_pretty_table, make_pretty_table_simple, transpose
from slither.printers.summary.halstead import compute_halstead
from slither.printers.summary.coupling import compute_coupling
from slither.printers.summary.loc import compute_loc_metrics
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
        if len(self.contracts) == 0:
            return self.generate_output("No contract found")
        txt = "\n\nComplexity dashboard\n\n"
        tables = []

        # LOC
        txt += "\nLines of code:\n"
        lines_dict = compute_loc_metrics(self.slither)
        headers = [""] + list(lines_dict.keys())
        report_dict = transpose(lines_dict)
        table = make_pretty_table(headers, report_dict)
        txt += str(table) + "\n"
        tables += [(table, "Lines of code")]

        # Cyclomatic complexity
        txt += "\nCyclomatic complexity:\n"
        cyclomatic_complexity_dict = make_cyclomatic_complexity_table(self.contracts)
        table = make_pretty_table(["Contract", "Cyclomatic complexity"], cyclomatic_complexity_dict, True)
        txt += str(table) + "\n"
        tables += [(table, "Cyclomatic complexity")]

        # Coupling Ca / Ce
        txt += "\nCoupling:\n"
        table = make_pretty_table(["Contract", "dependents_Ca", "dependencies_Ce"], compute_coupling(self.contracts))
        txt += str(table) + "\n"
        tables += [(table, "Coupling")]

        # Halstead
        core, extended1, extended2 = compute_halstead(self.contracts)

        # Halstead - Core metrics: operations and operands
        txt += "\nHalstead complexity core metrics:\n"
        keys = [k for k in core[self.contracts[0].name].keys()]
        table = make_pretty_table(["Contract", *keys], core, False)
        txt += str(table) + "\n"
        tables += [(table, "Halstead core metrics")]

        # Halstead - Extended metrics1: vocabulary, program length, estimated length, volume
        txt += "\nHalstead complexity extended metrics1:\n"
        keys = list(extended1[self.contracts[0].name].keys())
        table = make_pretty_table(["Contract", *keys], extended1, False)
        txt += str(table) + "\n"
        tables += [(table, "Halstead extended metrics1")]

        # Halstead - Extended metrics2: difficulty, effort, time, bugs
        txt += "\nHalstead complexity extended metrics2:\n"
        keys = list(extended2[self.contracts[0].name].keys())
        table = make_pretty_table(["Contract", *keys], extended2, False)
        txt += str(table) + "\n"
        tables += [(table, "Halstead extended metrics2")]



        # Project wide metrics

        # Create a dict of project wide metrics for display in a table
        # { "metric": <value>, ... }
        project_metrics = {}  # TODO: would be nice to have columns "overall", "contract min", "contract max", "contract avg"

        (abstract_contract_count, total_contract_count) = count_abstracts(self.contracts)
        total_functions = sum([len(contract.functions) for contract in self.contracts])

        project_metrics["SLOC (in src files)"] = lines_dict["src"]["sloc"]
        project_metrics["Number of contracts"] = total_contract_count
        project_metrics["Number of functions"] = total_functions
        project_metrics["Number of abstract contracts"] = abstract_contract_count
        abstractness = float(abstract_contract_count / total_contract_count)
        project_metrics["Abstractness"] = f"{abstractness:.3f}"
        project_metrics["Overall cyclomatic complexity"] = sum([cyclomatic_complexity_dict[contract.name]["Cyclomatic complexity"] for contract in self.contracts])
        totals_key = "ALL CONTRACTS" if len(self.contracts) > 1 else self.contracts[0].name
        project_metrics["Halstead volume"] = extended1[totals_key]["Volume"]
        project_metrics["Halstead difficulty"] = extended2[totals_key]["Difficulty"]



        # TODO: two printers - one with all details + summarys, one with summary only
        # All contracts summary
        # abstractness
        # cyclomatic complexity total
        # coupling maybe not (or maybe min max avg)?
        # halstead all contracts number
        # definitely code lines
        # other basic stuff like number of functions, number of contracts, etc

        table = make_pretty_table_simple(project_metrics, "Project metrics")
        txt += str(table) + "\n"
        tables += [(table, "Project metrics")]


        self.info(txt)
        res = self.generate_output(txt)
        for (table, title) in tables:
            res.add_pretty_table(table, title)
        return res
