import argparse
import logging
from typing import Optional, Dict
import os
import openai
from crytic_compile import cryticparser
from slither import Slither
from slither.core.compilation_unit import SlitherCompilationUnit

from slither.formatters.utils.patches import create_patch, apply_patch, create_diff

logging.basicConfig()
logging.getLogger("Slither").setLevel(logging.INFO)

logger = logging.getLogger("Slither-demo")


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

    # Add default arguments from crytic-compile
    cryticparser.init(parser)

    return parser.parse_args()


def _post_processesing(answer: str, starting_column: int) -> Optional[str]:
    """
    Clean answers from codex

    Args:
        answer:
        starting_column:

    Returns:

    """
    if answer.count("/**") != 1 or answer.count("*/") != 1:
        return None
    if answer.find("/**") > answer.find("*/"):
        return None
    answer = answer[answer.find("/**") : answer.find("*/") + 2]
    answer_lines = answer.splitlines()
    # Add indentation to all the lines, aside the first one
    if len(answer_lines) > 0:
        answer = (
            answer_lines[0]
            + "\n"
            + "\n".join([" " * (starting_column - 1) + line for line in answer_lines[1:] if line])
        )
        answer += "\n" + " " * (starting_column - 1)
        return answer
    return answer_lines[0]


def _handle_codex(answer: Dict, starting_column: int) -> Optional[str]:
    if "choices" in answer:
        if answer["choices"]:
            if "text" in answer["choices"][0]:
                answer_processed = _post_processesing(answer["choices"][0]["text"], starting_column)
                if answer_processed is None:
                    return None
                return answer_processed
    return None


# pylint: disable=too-many-locals
def _handle_compilation_unit(compilation_unit: SlitherCompilationUnit, overwrite: bool) -> None:
    all_patches: Dict = {}

    for function in compilation_unit.functions:
        if function.source_mapping.is_dependency or function.has_documentation:
            continue
        prompt = "Create a documentation for the solidity code using natspec (use only notice, dev, params, return)\n"
        src_mapping = function.source_mapping
        content = compilation_unit.core.source_code[src_mapping.filename.absolute]
        start = src_mapping.start
        end = src_mapping.start + src_mapping.length
        prompt += content[start:end]
        answer = openai.Completion.create(  # type: ignore
            model="text-davinci-003", prompt=prompt, temperature=0, max_tokens=200
        )

        answer_processed = _handle_codex(answer, src_mapping.starting_column)
        if answer_processed is None:
            print(f"Codex could not generate a well formatted answer for {function.canonical_name}")
            print(answer)
            continue

        create_patch(all_patches, src_mapping.filename.absolute, start, start, "", answer_processed)

    # cat math.sol
    # slither-documentation math.sol --overwrite
    # cat math.sol
    # exit
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

    slither = Slither(args.project, **vars(args))

    api_key = os.getenv("OPENAI_API_KEY")
    if api_key is None:
        print("Please provide an Open API Key (https://beta.openai.com/account/api-keys)")
        return
    openai.api_key = api_key

    for compilation_unit in slither.compilation_units:
        _handle_compilation_unit(compilation_unit, args.overwrite)


if __name__ == "__main__":
    main()
