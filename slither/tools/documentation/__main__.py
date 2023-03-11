import argparse
import logging
import uuid
from typing import Optional, Dict, List
from crytic_compile import cryticparser
from slither import Slither
from slither.core.compilation_unit import SlitherCompilationUnit
from slither.core.declarations import Function

from slither.formatters.utils.patches import create_patch, apply_patch, create_diff
from slither.utils import codex

logging.basicConfig()
logging.getLogger("Slither").setLevel(logging.INFO)

logger = logging.getLogger("Slither")


def parse_args() -> argparse.Namespace:
    """
    Parse the underlying arguments for the program.
    :return: Returns the arguments for the program.
    """
    parser = argparse.ArgumentParser(description="Demo", usage="slither-documentation filename")

    parser.add_argument("project", help="The target directory/Solidity file.")

    parser.add_argument(
        "--overwrite", help="Overwrite the files (be careful).", action="store_true", default=False
    )

    parser.add_argument(
        "--force-answer-parsing",
        help="Apply heuristics to better parse codex output (might lead to incorrect results)",
        action="store_true",
        default=False,
    )

    parser.add_argument(
        "--include-tests",
        help="Include the tests",
        action="store_true",
        default=False,
    )

    parser.add_argument(
        "--retry",
        help="Retry failed query (default 1). Each retry increases the temperature by 0.1",
        action="store",
        default=1,
    )

    # Add default arguments from crytic-compile
    cryticparser.init(parser)

    codex.init_parser(parser, always_enable_codex=True)

    return parser.parse_args()


def _use_tab(char: str) -> Optional[bool]:
    """
    Check if the char is a tab

    Args:
        char:

    Returns:

    """
    if char == " ":
        return False
    if char == "\t":
        return True
    return None


def _post_processesing(
    answer: str, starting_column: int, use_tab: Optional[bool], force_and_stopped: bool
) -> Optional[str]:
    """
    Clean answers from codex

    Args:
        answer:
        starting_column:

    Returns:

    """
    if answer.count("/**") != 1:
        return None
    # Sometimes codex will miss the */, even if it finished properly the request
    # In this case, we allow slither-documentation to force the */
    if answer.count("*/") != 1:
        if force_and_stopped:
            answer += "*/"
        else:
            return None
    if answer.find("/**") > answer.find("*/"):
        return None
    answer = answer[answer.find("/**") : answer.find("*/") + 2]
    answer_lines = answer.splitlines()
    # Add indentation to all the lines, aside the first one

    space_char = "\t" if use_tab else " "

    if len(answer_lines) > 0:
        answer = (
            answer_lines[0]
            + "\n"
            + "\n".join(
                [space_char * (starting_column - 1) + line for line in answer_lines[1:] if line]
            )
        )
        answer += "\n" + space_char * (starting_column - 1)
        return answer
    return answer_lines[0]


def _handle_codex(
    answer: Dict, starting_column: int, use_tab: Optional[bool], force: bool
) -> Optional[str]:
    if "choices" in answer:
        if answer["choices"]:
            if "text" in answer["choices"][0]:
                has_stopped = answer["choices"][0].get("finish_reason", "") == "stop"
                answer_processed = _post_processesing(
                    answer["choices"][0]["text"], starting_column, use_tab, force and has_stopped
                )
                if answer_processed is None:
                    return None
                return answer_processed
    return None


# pylint: disable=too-many-locals,too-many-arguments
def _handle_function(
    function: Function,
    overwrite: bool,
    all_patches: Dict,
    logging_file: Optional[str],
    slither: Slither,
    retry: int,
    force: bool,
) -> bool:
    if (
        function.source_mapping.is_dependency
        or function.has_documentation
        or function.is_constructor_variables
    ):
        return overwrite
    prompt = "Create a natpsec documentation for this solidity code with only notice and dev.\n"
    src_mapping = function.source_mapping
    content = function.compilation_unit.core.source_code[src_mapping.filename.absolute]
    start = src_mapping.start
    end = src_mapping.start + src_mapping.length
    prompt += content[start:end]

    use_tab = _use_tab(content[start - 1])
    if use_tab is None and src_mapping.starting_column > 1:
        logger.info(f"Non standard space indentation found {content[start - 1:end]}")
        if overwrite:
            logger.info("Disable overwrite to avoid mistakes")
            overwrite = False

    openai = codex.openai_module()  # type: ignore
    if openai is None:
        raise ImportError

    if logging_file:
        codex.log_codex(logging_file, "Q: " + prompt)

    tentative = 0
    answer_processed: Optional[str] = None
    while tentative < retry:
        tentative += 1

        answer = openai.Completion.create(  # type: ignore
            prompt=prompt,
            model=slither.codex_model,
            temperature=min(slither.codex_temperature + tentative * 0.1, 1),
            max_tokens=slither.codex_max_tokens,
        )

        if logging_file:
            codex.log_codex(logging_file, "A: " + str(answer))

        answer_processed = _handle_codex(answer, src_mapping.starting_column, use_tab, force)
        if answer_processed:
            break

        logger.info(
            f"Codex could not generate a well formatted answer for {function.canonical_name}"
        )
        logger.info(answer)

    if not answer_processed:
        return overwrite

    create_patch(all_patches, src_mapping.filename.absolute, start, start, "", answer_processed)

    return overwrite


def _handle_compilation_unit(
    slither: Slither,
    compilation_unit: SlitherCompilationUnit,
    overwrite: bool,
    force: bool,
    retry: int,
    include_test: bool,
) -> None:
    logging_file: Optional[str]
    if slither.codex_log:
        logging_file = str(uuid.uuid4())
    else:
        logging_file = None

    for scope in compilation_unit.scopes.values():
        # Dont send tests file
        if not include_test and (
            ".t.sol" in scope.filename.absolute
            or "mock" in scope.filename.absolute.lower()
            or "test" in scope.filename.absolute.lower()
        ):
            continue

        functions_target: List[Function] = []

        for contract in scope.contracts.values():
            functions_target += contract.functions_declared

        functions_target += list(scope.functions)

        all_patches: Dict = {}

        for function in functions_target:
            overwrite = _handle_function(
                function, overwrite, all_patches, logging_file, slither, retry, force
            )

        # all_patches["patches"] should have only 1 file
        if "patches" not in all_patches:
            continue
        for file in all_patches["patches"]:
            original_txt = compilation_unit.core.source_code[file].encode("utf8")
            patched_txt = original_txt

            patches = all_patches["patches"][file]
            offset = 0
            patches.sort(key=lambda x: x["start"])

            for patch in patches:
                patched_txt, offset = apply_patch(patched_txt, patch, offset)

            if overwrite:
                with open(file, "w", encoding="utf8") as f:
                    f.write(patched_txt.decode("utf8"))
            else:
                diff = create_diff(compilation_unit, original_txt, patched_txt, file)
                with open(f"{file}.patch", "w", encoding="utf8") as f:
                    f.write(diff)


def main() -> None:
    args = parse_args()

    logger.info("This tool is a WIP, use it with cautious")
    logger.info("Be aware of OpenAI ToS: https://openai.com/api/policies/terms/")
    slither = Slither(args.project, **vars(args))

    try:
        for compilation_unit in slither.compilation_units:
            _handle_compilation_unit(
                slither,
                compilation_unit,
                args.overwrite,
                args.force_answer_parsing,
                int(args.retry),
                args.include_tests,
            )
    except ImportError:
        pass


if __name__ == "__main__":
    main()
