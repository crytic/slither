from typing import List, Union, Dict, Type

from slither.tools.upgradeability.checks.abstract_checks import classification_txt, AbstractCheck
from slither.utils.myprettytable import MyPrettyTable


def output_wiki(detector_classes: List[Type[AbstractCheck]], filter_wiki: str) -> None:
    # Sort by impact, confidence, and name
    detectors_list = sorted(
        detector_classes, key=lambda element: (element.IMPACT, element.ARGUMENT)
    )

    for detector in detectors_list:
        if filter_wiki not in detector.WIKI:
            continue
        argument = detector.ARGUMENT
        impact = classification_txt[detector.IMPACT]
        title = detector.WIKI_TITLE
        description = detector.WIKI_DESCRIPTION
        exploit_scenario = detector.WIKI_EXPLOIT_SCENARIO
        recommendation = detector.WIKI_RECOMMENDATION

        print(f"\n## {title}")
        print("### Configuration")
        print(f"* Check: `{argument}`")
        print(f"* Severity: `{impact}`")
        print("\n### Description")
        print(description)
        if exploit_scenario:
            print("\n### Exploit Scenario:")
            print(exploit_scenario)
        print("\n### Recommendation")
        print(recommendation)


def output_detectors(detector_classes: List[Type[AbstractCheck]]) -> None:
    detectors_list = []
    for detector in detector_classes:
        argument = detector.ARGUMENT
        help_info = detector.HELP
        impact = detector.IMPACT
        require_proxy = detector.REQUIRE_PROXY
        require_v2 = detector.REQUIRE_CONTRACT_V2
        detectors_list.append((argument, help_info, impact, require_proxy, require_v2))
    table = MyPrettyTable(["Num", "Check", "What it Detects", "Impact", "Proxy", "Contract V2"])

    # Sort by impact, confidence, and name
    detectors_list = sorted(detectors_list, key=lambda element: (element[2], element[0]))
    idx = 1
    for (argument, help_info, impact, proxy, v2) in detectors_list:
        table.add_row(
            [
                str(idx),
                argument,
                help_info,
                classification_txt[impact],
                "X" if proxy else "",
                "X" if v2 else "",
            ]
        )
        idx = idx + 1
    print(table)


def output_to_markdown(detector_classes: List[Type[AbstractCheck]], _filter_wiki: str) -> None:
    def extract_help(cls: Type[AbstractCheck]) -> str:
        if cls.WIKI == "":
            return cls.HELP
        return f"[{cls.HELP}]({cls.WIKI})"

    detectors_list = []
    for detector in detector_classes:
        argument = detector.ARGUMENT
        help_info = extract_help(detector)
        impact = detector.IMPACT
        require_proxy = detector.REQUIRE_PROXY
        require_v2 = detector.REQUIRE_CONTRACT_V2
        detectors_list.append((argument, help_info, impact, require_proxy, require_v2))

    # Sort by impact, confidence, and name
    detectors_list = sorted(detectors_list, key=lambda element: (element[2], element[0]))
    idx = 1
    for (argument, help_info, impact, proxy, v2) in detectors_list:
        print(
            f"{idx} | `{argument}` | {help_info} | {classification_txt[impact]} | {'X' if proxy else ''} | {'X' if v2 else ''}"
        )
        idx = idx + 1


def output_detectors_json(
    detector_classes: List[Type[AbstractCheck]],
) -> List[Dict[str, Union[str, int]]]:
    detectors_list = []
    for detector in detector_classes:
        argument = detector.ARGUMENT
        help_info = detector.HELP
        impact = detector.IMPACT
        wiki_url = detector.WIKI
        wiki_description = detector.WIKI_DESCRIPTION
        wiki_exploit_scenario = detector.WIKI_EXPLOIT_SCENARIO
        wiki_recommendation = detector.WIKI_RECOMMENDATION
        detectors_list.append(
            (
                argument,
                help_info,
                impact,
                wiki_url,
                wiki_description,
                wiki_exploit_scenario,
                wiki_recommendation,
            )
        )

    # Sort by impact, confidence, and name
    detectors_list = sorted(detectors_list, key=lambda element: (element[2], element[0]))
    idx = 1
    table: List[Dict[str, Union[str, int]]] = []
    for (
        argument,
        help_info,
        impact,
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
                "wiki_url": wiki_url,
                "description": description,
                "exploit_scenario": exploit,
                "recommendation": recommendation,
            }
        )
        idx = idx + 1
    return table
