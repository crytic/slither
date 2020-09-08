from slither.utils.myprettytable import MyPrettyTable


def output_mutators(mutators_classes):
    mutators_list = []
    for detector in mutators_classes:
        argument = detector.NAME
        help_info = detector.HELP
        fault_class = detector.FAULTCLASS.name
        fault_nature = detector.FAULTNATURE.name
        mutators_list.append((argument, help_info, fault_class, fault_nature))
    table = MyPrettyTable(["Num", "Name", "What it Does", "Fault Class", "Fault Nature"])

    # Sort by class, nature, name
    mutators_list = sorted(mutators_list, key=lambda element: (element[2], element[3], element[0]))
    idx = 1
    for (argument, help_info, fault_class, fault_nature) in mutators_list:
        table.add_row([idx, argument, help_info, fault_class, fault_nature])
        idx = idx + 1
    print(table)
