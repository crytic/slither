from slither.tools.mutator.mutators.abstract_mutator import AbstractMutator
from slither.utils.myprettytable import MyPrettyTable


def output_mutators(mutators_classes: list[type[AbstractMutator]]) -> None:
    mutators_list = []
    for detector in mutators_classes:
        argument = detector.NAME
        help_info = detector.HELP
        mutators_list.append((argument, help_info))
    table = MyPrettyTable(["Num", "Name", "What it Does"])

    # Sort by class
    mutators_list = sorted(mutators_list, key=lambda element: (element[0]))
    idx = 1
    for argument, help_info in mutators_list:
        table.add_row([str(idx), argument, help_info])
        idx = idx + 1
    print(table)
