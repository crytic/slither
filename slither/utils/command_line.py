from prettytable import PrettyTable

from slither.detectors.abstract_detector import classification_txt

def output_to_markdown(detector_classes, printer_classes):

    def extract_help(detector):
        if detector.WIKI == '':
            return detector.HELP
        return '[{}]({})'.format(detector.HELP, detector.WIKI)

    detectors_list = []
    for detector in detector_classes:
        argument = detector.ARGUMENT
        # dont show the backdoor example
        if argument == 'backdoor':
            continue
        help_info = extract_help(detector)
        impact = detector.IMPACT
        confidence = classification_txt[detector.CONFIDENCE]
        detectors_list.append((argument, help_info, impact, confidence))

    # Sort by impact, confidence, and name
    detectors_list = sorted(detectors_list, key=lambda element: (element[2], element[3], element[0]))
    idx = 1
    for (argument, help_info, impact, confidence) in detectors_list:
        print('{} | `{}` | {} | {} | {}'.format(idx,
                                                argument,
                                                help_info,
                                                classification_txt[impact],
                                                confidence))
        idx = idx + 1

    print()
    printers_list = []
    for printer in printer_classes:
        argument = printer.ARGUMENT
        help_info = printer.HELP
        printers_list.append((argument, help_info))

    # Sort by impact, confidence, and name
    printers_list = sorted(printers_list, key=lambda element: (element[0]))
    idx = 1
    for (argument, help_info) in printers_list:
        print('{} | `{}` | {}'.format(idx, argument, help_info))
        idx = idx + 1

def output_detectors(detector_classes):
    detectors_list = []
    for detector in detector_classes:
        argument = detector.ARGUMENT
        # dont show the backdoor example
        if argument == 'backdoor':
            continue
        help_info = detector.HELP
        impact = detector.IMPACT
        confidence = classification_txt[detector.CONFIDENCE]
        detectors_list.append((argument, help_info, impact, confidence))
    table = PrettyTable(["Num",
                         "Check",
                         "What it Detects",
                         "Impact",
                         "Confidence"])

    # Sort by impact, confidence, and name
    detectors_list = sorted(detectors_list, key=lambda element: (element[2], element[3], element[0]))
    idx = 1
    for (argument, help_info, impact, confidence) in detectors_list:
        table.add_row([idx, argument, help_info, classification_txt[impact], confidence])
        idx = idx + 1
    print(table)

def output_printers(printer_classes):
    printers_list = []
    for printer in printer_classes:
        argument = printer.ARGUMENT
        help_info = printer.HELP
        printers_list.append((argument, help_info))
    table = PrettyTable(["Num",
                         "Printer",
                         "What it Does"])

    # Sort by impact, confidence, and name
    printers_list = sorted(printers_list, key=lambda element: (element[0]))
    idx = 1
    for (argument, help_info) in printers_list:
        table.add_row([idx, argument, help_info])
        idx = idx + 1
    print(table)
