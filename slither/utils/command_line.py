import argparse
import enum
import json
import os
import re
import logging
from collections import defaultdict
from typing import Dict, List, Type, Union

from crytic_compile.cryticparser.defaults import (
    DEFAULTS_FLAG_IN_CONFIG as DEFAULTS_FLAG_IN_CONFIG_CRYTIC_COMPILE,
)

from slither.detectors.abstract_detector import classification_txt, AbstractDetector
from slither.printers.abstract_printer import AbstractPrinter
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


class FailOnLevel(enum.Enum):
    PEDANTIC = "pedantic"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    NONE = "none"


# Those are the flags shared by the command line and the config file
defaults_flag_in_config = {
    "codex": False,
    "codex_contracts": "all",
    "codex_model": "text-davinci-003",
    "codex_temperature": 0,
    "codex_max_tokens": 300,
    "codex_log": False,
    "detectors_to_run": "all",
    "printers_to_run": None,
    "detectors_to_exclude": None,
    "exclude_dependencies": False,
    "exclude_informational": False,
    "exclude_optimization": False,
    "exclude_low": False,
    "exclude_medium": False,
    "exclude_high": False,
    "fail_on": FailOnLevel.PEDANTIC,
    "json": None,
    "sarif": None,
    "json-types": ",".join(DEFAULT_JSON_OUTPUT_TYPES),
    "disable_color": False,
    "filter_paths": None,
    "generate_patches": False,
    # debug command
    "skip_assembly": False,
    "legacy_ast": False,
    "zip": None,
    "zip_type": "lzma",
    "show_ignored_findings": False,
    "no_fail": False,
    "sarif_input": "export.sarif",
    "sarif_triage": "export.sarif.sarifexplorer",
    **DEFAULTS_FLAG_IN_CONFIG_CRYTIC_COMPILE,
}

deprecated_flags = {
    "fail_pedantic": True,
    "fail_low": False,
    "fail_medium": False,
    "fail_high": False,
}


def read_config_file(args: argparse.Namespace) -> None:
    # No config file was provided as an argument
    if args.config_file is None:
        # Check wether the default config file is present
        if os.path.exists("slither.config.json"):
            # The default file exists, use it
            args.config_file = "slither.config.json"
        else:
            return

    if os.path.isfile(args.config_file):
        try:
            with open(args.config_file, encoding="utf8") as f:
                config = json.load(f)
                for key, elem in config.items():
                    if key in deprecated_flags:
                        logger.info(
                            yellow(f"{args.config_file} has a deprecated key: {key} : {elem}")
                        )
                        migrate_config_options(args, key, elem)
                        continue
                    if key not in defaults_flag_in_config:
                        logger.info(
                            yellow(f"{args.config_file} has an unknown key: {key} : {elem}")
                        )
                        continue
                    if getattr(args, key) == defaults_flag_in_config[key]:
                        setattr(args, key, elem)
        except json.decoder.JSONDecodeError as e:
            logger.error(red(f"Impossible to read {args.config_file}, please check the file {e}"))
    else:
        logger.error(red(f"File {args.config_file} is not a file or does not exist"))
        logger.error(yellow("Falling back to the default settings..."))


def migrate_config_options(args: argparse.Namespace, key: str, elem):
    if key.startswith("fail_") and getattr(args, "fail_on") == defaults_flag_in_config["fail_on"]:
        if key == "fail_pedantic":
            pedantic_setting = elem
            fail_on = FailOnLevel.PEDANTIC if pedantic_setting else FailOnLevel.NONE
            setattr(args, "fail_on", fail_on)
            logger.info(f"Migrating fail_pedantic: {pedantic_setting} as fail_on: {fail_on.value}")
        elif key == "fail_low" and elem is True:
            logger.info("Migrating fail_low: true -> fail_on: low")
            setattr(args, "fail_on", FailOnLevel.LOW)

        elif key == "fail_medium" and elem is True:
            logger.info("Migrating fail_medium: true -> fail_on: medium")
            setattr(args, "fail_on", FailOnLevel.MEDIUM)

        elif key == "fail_high" and elem is True:
            logger.info("Migrating fail_high: true -> fail_on: high")
            setattr(args, "fail_on", FailOnLevel.HIGH)
        else:
            logger.warning(yellow(f"Key {key} was deprecated but no migration was provided"))


def output_to_markdown(
    detector_classes: List[Type[AbstractDetector]],
    printer_classes: List[Type[AbstractPrinter]],
    filter_wiki: str,
) -> None:
    def extract_help(cls: Union[Type[AbstractDetector], Type[AbstractPrinter]]) -> str:
        if cls.WIKI == "":
            return cls.HELP
        return f"[{cls.HELP}]({cls.WIKI})"

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
        print(f"{idx} | `{argument}` | {help_info} | {classification_txt[impact]} | {confidence}")
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
        print(f"{idx} | `{argument}` | {help_info}")
        idx = idx + 1


def get_level(l: str) -> int:
    tab = l.count("\t") + 1
    if l.replace("\t", "").startswith(" -"):
        tab = tab + 1
    if l.replace("\t", "").startswith("-"):
        tab = tab + 1
    return tab


def convert_result_to_markdown(txt: str) -> str:
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


def output_results_to_markdown(
    all_results: List[Dict], checklistlimit: str, show_ignored_findings: bool
) -> None:
    checks = defaultdict(list)
    info: Dict = defaultdict(dict)
    for results_ in all_results:
        checks[results_["check"]].append(results_)
        info[results_["check"]] = {
            "impact": results_["impact"],
            "confidence": results_["confidence"],
        }

    if not show_ignored_findings:
        print(
            "**THIS CHECKLIST IS NOT COMPLETE**. Use `--show-ignored-findings` to show all the results."
        )

    print("Summary")
    for check_ in checks:
        print(
            f" - [{check_}](#{check_}) ({len(checks[check_])} results) ({info[check_]['impact']})"
        )

    counter = 0
    for (check, results) in checks.items():
        print(f"## {check}")
        print(f'Impact: {info[check]["impact"]}')
        print(f'Confidence: {info[check]["confidence"]}')
        additional = False
        if checklistlimit and len(results) > 5:
            results = results[0:5]
            additional = True
        for result in results:
            print(" - [ ] ID-" + f"{counter}")
            counter = counter + 1
            print(result["markdown"])
            if result["first_markdown_element"]:
                print(result["first_markdown_element"])
                print("\n")
        if additional:
            print(f"**More results were found, check [{checklistlimit}]({checklistlimit})**")


def output_wiki(detector_classes: List[Type[AbstractDetector]], filter_wiki: str) -> None:

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

        print(f"\n## {title}")
        print("### Configuration")
        print(f"* Check: `{check}`")
        print(f"* Severity: `{impact}`")
        print(f"* Confidence: `{confidence}`")
        print("\n### Description")
        print(description)
        if exploit_scenario:
            print("\n### Exploit Scenario:")
            print(exploit_scenario)
        print("\n### Recommendation")
        print(recommendation)


def output_detectors(detector_classes: List[Type[AbstractDetector]]) -> None:
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
        table.add_row([str(idx), argument, help_info, classification_txt[impact], confidence])
        idx = idx + 1
    print(table)


# pylint: disable=too-many-locals
def output_detectors_json(
    detector_classes: List[Type[AbstractDetector]],
) -> List[Dict]:
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


def output_printers(printer_classes: List[Type[AbstractPrinter]]) -> None:
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
        table.add_row([str(idx), argument, help_info])
        idx = idx + 1
    print(table)


def output_printers_json(printer_classes: List[Type[AbstractPrinter]]) -> List[Dict]:
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


def check_and_sanitize_markdown_root(markdown_root: str) -> str:
    # Regex to check whether the markdown_root is a GitHub URL
    match = re.search(
        r"(https://)github.com/([a-zA-Z-]+)([:/][A-Za-z0-9_.-]+[:/]?)([A-Za-z0-9_.-]*)(.*)",
        markdown_root,
    )
    if match:
        if markdown_root[-1] != "/":
            logger.warning("Appending '/' in markdown_root url for better code referencing")
            markdown_root = markdown_root + "/"

        if not match.group(4):
            logger.warning(
                "Appending 'master/tree/' in markdown_root url for better code referencing"
            )
            markdown_root = markdown_root + "master/tree/"
        elif match.group(4) == "tree":
            logger.warning(
                "Replacing 'tree' with 'blob' in markdown_root url for better code referencing"
            )
            positions = match.span(4)
            markdown_root = f"{markdown_root[:positions[0]]}blob{markdown_root[positions[1]:]}"

    return markdown_root
