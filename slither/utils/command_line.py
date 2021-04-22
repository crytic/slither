import json
import os
import logging
from collections import defaultdict
from crytic_compile.cryticparser.defaults import (
    DEFAULTS_FLAG_IN_CONFIG as DEFAULTS_FLAG_IN_CONFIG_CRYTIC_COMPILE,
)

from slither.detectors.abstract_detector import classification_txt
from slither.utils.colors import yellow, red
from slither.utils.myprettytable import MyPrettyTable

logger = logging.getLogger("Slither")

DEFAULT_JSON_OUTPUT_TYPES = ["detectors", "printers"]
JSON_OUTPUT_TYPES = [
    "compilations",
    "console",
    "detectors",
    "printers",
    "list-detectors",
    "list-printers",
]

# Those are the flags shared by the command line and the config file
defaults_flag_in_config = {
    "detectors_to_run": "all",
    "printers_to_run": None,
    "detectors_to_exclude": None,
    "exclude_dependencies": False,
    "exclude_informational": False,
    "exclude_optimization": False,
    "exclude_low": False,
    "exclude_medium": False,
    "exclude_high": False,
    "json": None,
    "json-types": ",".join(DEFAULT_JSON_OUTPUT_TYPES),
    "disable_color": False,
    "filter_paths": None,
    "generate_patches": False,
    # debug command
    "skip_assembly": False,
    "legacy_ast": False,
    "ignore_return_value": False,
    "zip": None,
    "zip_type": "lzma",
    "show_ignored_findings": False,
    **DEFAULTS_FLAG_IN_CONFIG_CRYTIC_COMPILE,
}


def read_config_file(args):
    if os.path.isfile(args.config_file):
        try:
            with open(args.config_file) as f:
                config = json.load(f)
                for key, elem in config.items():
                    if key not in defaults_flag_in_config:
                        logger.info(
                            yellow(
                                "{} has an unknown key: {} : {}".format(args.config_file, key, elem)
                            )
                        )
                        continue
                    if getattr(args, key) == defaults_flag_in_config[key]:
                        setattr(args, key, elem)
        except json.decoder.JSONDecodeError as e:
            logger.error(
                red("Impossible to read {}, please check the file {}".format(args.config_file, e))
            )


def output_to_markdown(detector_classes, printer_classes, filter_wiki):
    def extract_help(cls):
        if cls.WIKI == "":
            return cls.HELP
        return "[{}]({})".format(cls.HELP, cls.WIKI)

    detectors_list = []
    print(filter_wiki)
    for detector in detector_classes:
        argument = detector.ARGUMENT
        # dont show the backdoor example
        if argument == "backdoor":
            continue
        if not filter_wiki in detector.WIKI:
            continue
        help_info = extract_help(detector)
        impact = detector.IMPACT
        confidence = classification_txt[detector.CONFIDENCE]
        detectors_list.append((argument, help_info, impact, confidence))

    # Sort by impact, confidence, and name
    detectors_list = sorted(
        detectors_list, key=lambda element: (element[2], element[3], element[0])
    )
    idx = 1
    for (argument, help_info, impact, confidence) in detectors_list:
        print(
            "{} | `{}` | {} | {} | {}".format(
                idx, argument, help_info, classification_txt[impact], confidence
            )
        )
        idx = idx + 1

    print()
    printers_list = []
    for printer in printer_classes:
        argument = printer.ARGUMENT
        help_info = extract_help(printer)
        printers_list.append((argument, help_info))

    # Sort by impact, confidence, and name
    printers_list = sorted(printers_list, key=lambda element: (element[0]))
    idx = 1
    for (argument, help_info) in printers_list:
        print("{} | `{}` | {}".format(idx, argument, help_info))
        idx = idx + 1


def get_level(l):
    tab = l.count("\t") + 1
    if l.replace("\t", "").startswith(" -"):
        tab = tab + 1
    if l.replace("\t", "").startswith("-"):
        tab = tab + 1
    return tab


def convert_result_to_markdown(txt):
    # -1 to remove the last \n
    lines = txt[0:-1].split("\n")
    ret = []
    level = 0
    for l in lines:
        next_level = get_level(l)
        prefix = "<li>"
        if next_level < level:
            prefix = "</ul>" * (level - next_level) + prefix
        if next_level > level:
            prefix = "<ul>" * (next_level - level) + prefix
        level = next_level
        ret.append(prefix + l)

    return "".join(ret)


def output_results_to_markdown(all_results):
    checks = defaultdict(list)
    info = defaultdict(dict)
    for results in all_results:
        checks[results["check"]].append(results)
        info[results["check"]] = {"impact": results["impact"], "confidence": results["confidence"]}

    print("Summary")
    for check in checks:
        print(f" - [{check}](#{check}) ({len(checks[check])} results)")

    counter = 0
    for (check, results) in checks.items():
        print(f"## {check}")
        print(f'Impact: {info[check]["impact"]}')
        print(f'Confidence: {info[check]["confidence"]}')
        for result in results:
            print(" - [ ] ID-" + f"{counter}")
            counter = counter + 1
            print(result["markdown"])
            if result["first_markdown_element"]:
                print(result["first_markdown_element"])
                print("\n")


def output_wiki(detector_classes, filter_wiki):
    detectors_list = []

    # Sort by impact, confidence, and name
    detectors_list = sorted(
        detector_classes,
        key=lambda element: (element.IMPACT, element.CONFIDENCE, element.ARGUMENT),
    )

    for detector in detectors_list:
        argument = detector.ARGUMENT
        # dont show the backdoor example
        if argument == "backdoor":
            continue
        if not filter_wiki in detector.WIKI:
            continue
        check = detector.ARGUMENT
        impact = classification_txt[detector.IMPACT]
        confidence = classification_txt[detector.CONFIDENCE]
        title = detector.WIKI_TITLE
        description = detector.WIKI_DESCRIPTION
        exploit_scenario = detector.WIKI_EXPLOIT_SCENARIO
        recommendation = detector.WIKI_RECOMMENDATION

        print("\n## {}".format(title))
        print("### Configuration")
        print("* Check: `{}`".format(check))
        print("* Severity: `{}`".format(impact))
        print("* Confidence: `{}`".format(confidence))
        print("\n### Description")
        print(description)
        if exploit_scenario:
            print("\n### Exploit Scenario:")
            print(exploit_scenario)
        print("\n### Recommendation")
        print(recommendation)


def output_detectors(detector_classes):
    detectors_list = []
    for detector in detector_classes:
        argument = detector.ARGUMENT
        # dont show the backdoor example
        if argument == "backdoor":
            continue
        help_info = detector.HELP
        impact = detector.IMPACT
        confidence = classification_txt[detector.CONFIDENCE]
        detectors_list.append((argument, help_info, impact, confidence))
    table = MyPrettyTable(["Num", "Check", "What it Detects", "Impact", "Confidence"])

    # Sort by impact, confidence, and name
    detectors_list = sorted(
        detectors_list, key=lambda element: (element[2], element[3], element[0])
    )
    idx = 1
    for (argument, help_info, impact, confidence) in detectors_list:
        table.add_row([idx, argument, help_info, classification_txt[impact], confidence])
        idx = idx + 1
    print(table)


def output_detectors_json(detector_classes):  # pylint: disable=too-many-locals
    detectors_list = []
    for detector in detector_classes:
        argument = detector.ARGUMENT
        # dont show the backdoor example
        if argument == "backdoor":
            continue
        help_info = detector.HELP
        impact = detector.IMPACT
        confidence = classification_txt[detector.CONFIDENCE]
        wiki_url = detector.WIKI
        wiki_description = detector.WIKI_DESCRIPTION
        wiki_exploit_scenario = detector.WIKI_EXPLOIT_SCENARIO
        wiki_recommendation = detector.WIKI_RECOMMENDATION
        detectors_list.append(
            (
                argument,
                help_info,
                impact,
                confidence,
                wiki_url,
                wiki_description,
                wiki_exploit_scenario,
                wiki_recommendation,
            )
        )

    # Sort by impact, confidence, and name
    detectors_list = sorted(
        detectors_list, key=lambda element: (element[2], element[3], element[0])
    )
    idx = 1
    table = []
    for (
        argument,
        help_info,
        impact,
        confidence,
        wiki_url,
        description,
        exploit,
        recommendation,
    ) in detectors_list:
        table.append(
            {
                "index": idx,
                "check": argument,
                "title": help_info,
                "impact": classification_txt[impact],
                "confidence": confidence,
                "wiki_url": wiki_url,
                "description": description,
                "exploit_scenario": exploit,
                "recommendation": recommendation,
            }
        )
        idx = idx + 1
    return table


def output_printers(printer_classes):
    printers_list = []
    for printer in printer_classes:
        argument = printer.ARGUMENT
        help_info = printer.HELP
        printers_list.append((argument, help_info))
    table = MyPrettyTable(["Num", "Printer", "What it Does"])

    # Sort by impact, confidence, and name
    printers_list = sorted(printers_list, key=lambda element: (element[0]))
    idx = 1
    for (argument, help_info) in printers_list:
        table.add_row([idx, argument, help_info])
        idx = idx + 1
    print(table)


def output_printers_json(printer_classes):
    printers_list = []
    for printer in printer_classes:
        argument = printer.ARGUMENT
        help_info = printer.HELP

        printers_list.append((argument, help_info))

    # Sort by name
    printers_list = sorted(printers_list, key=lambda element: (element[0]))
    idx = 1
    table = []
    for (argument, help_info) in printers_list:
        table.append({"index": idx, "check": argument, "title": help_info})
        idx = idx + 1
    return table
