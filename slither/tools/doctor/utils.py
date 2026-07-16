from contextlib import contextmanager
import logging
from slither.utils.colors import bold, yellow, red


@contextmanager
def snip_section(message: str | None) -> None:
    if message:
        print(red(message), end="\n\n")

    print(yellow("---- snip 8< ----"))
    yield
    print(yellow("---- >8 snip ----"))


@contextmanager
def report_section(title: str) -> None:
    print(bold(f"## {title}"), end="\n\n")
    try:
        yield
    except Exception as e:
        with snip_section(
            "slither-doctor failed unexpectedly! Please report this on the Slither GitHub issue tracker, and include the output below:"
        ):
            logging.exception(e)
    finally:
        print(end="\n\n")
