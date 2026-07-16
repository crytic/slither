from crytic_compile import CryticCompile
from slither.core.declarations import (
    Contract,
    FunctionContract,
)
from slither.core.source_mapping.source_mapping import Source, SourceMapping
from slither.exceptions import SlitherError


def get_definition(target: SourceMapping, crytic_compile: CryticCompile) -> Source:
    try:
        pattern = target.pattern
    except AttributeError as exc:
        raise SlitherError(f"get_definition_generic not implemented for {type(target)}") from exc

    file_content = crytic_compile.src_content_for_file(target.source_mapping.filename.absolute)
    txt = file_content[
        target.source_mapping.start : target.source_mapping.start + target.source_mapping.length
    ]

    start_offset = txt.find(pattern) + 1  # remove the space

    starting_line, starting_column = crytic_compile.get_line_from_offset(
        target.source_mapping.filename, target.source_mapping.start + start_offset
    )

    ending_line, ending_column = crytic_compile.get_line_from_offset(
        target.source_mapping.filename, target.source_mapping.start + start_offset + len(pattern)
    )

    s = Source(target.source_mapping.compilation_unit)
    s.start = target.source_mapping.start + start_offset
    s.length = len(pattern)
    s.filename = target.source_mapping.filename
    s.is_dependency = target.source_mapping.is_dependency
    s.lines = list(range(starting_line, ending_line + 1))
    s.starting_column = starting_column
    s.ending_column = ending_column
    s.end = s.start + s.length
    s.txt = txt
    return s


def get_implementation(target: SourceMapping) -> Source:
    return target.source_mapping


def get_all_implementations(target: SourceMapping, contracts: list[Contract]) -> set[Source]:
    """
    Get all implementations of a contract or function, accounting for inheritance and overrides
    """
    implementations = set()
    # Abstract contracts and interfaces are implemented by their children
    if isinstance(target, Contract):
        is_interface = target.is_interface
        is_implicitly_abstract = not target.is_fully_implemented
        is_explicitly_abstract = target.is_abstract
        if is_interface or is_implicitly_abstract or is_explicitly_abstract:
            for contract in contracts:
                if target in contract.immediate_inheritance:
                    implementations.add(contract.source_mapping)

    # Parent's virtual functions may be overridden by children
    elif isinstance(target, FunctionContract):
        for over in target.overridden_by:
            implementations.add(over.source_mapping)
        # Only show implemented virtual functions
        if not target.is_virtual or target.is_implemented:
            implementations.add(get_implementation(target))

    else:
        implementations.add(get_implementation(target))

    return implementations


def get_references(target: SourceMapping) -> list[Source]:
    return target.references
