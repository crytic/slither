"""Regression guard: the dead ``LogMessages`` constant bag stays deleted.

The data-flow logger used to ship a ``LogMessages`` class holding ~25 message
template constants, re-exported from ``slither.analyses.data_flow.logger``'s
``__all__``. Nothing in the repository ever referenced it: call sites passed
their own literal templates, so the class was documentation that could drift
away from reality without any test noticing.

These tests pin its removal from three angles — the implementation module, the
package namespace, and the shipped source tree — so a well-meaning
reintroduction has to be a deliberate change to this file rather than a silent
regrowth of dead code.

None of these tests build or reconfigure a :class:`DataFlowLogger`, so no
loguru sinks are added or removed and the module-level ``_logger_instance``
singleton is never touched. Importing the logger module has no side effects:
it only defines constants, functions, and classes.
"""

from __future__ import annotations

import importlib
from pathlib import Path

import slither.analyses.data_flow
from slither.analyses.data_flow import logger as logger_package
from slither.analyses.data_flow.logger import logger as logger_module

DEAD_SYMBOL = "LogMessages"


def test_implementation_module_defines_no_log_messages() -> None:
    """The class is gone from ``...logger.logger`` itself."""
    assert not hasattr(logger_module, DEAD_SYMBOL), (
        f"{DEAD_SYMBOL} was reintroduced in {logger_module.__name__}; it is a bag of "
        "unused message constants. Log call sites pass their own templates."
    )


def test_package_namespace_exposes_no_log_messages() -> None:
    """The class is not re-exported into the ``logger`` package namespace.

    Resolving the package through :func:`importlib.import_module` as well as the
    top-level ``from`` import checks the same object by both routes, so a
    reintroduction cannot hide behind whichever one a caller happens to use.
    """
    resolved = importlib.import_module("slither.analyses.data_flow.logger")

    assert resolved is logger_package
    assert getattr(resolved, DEAD_SYMBOL, None) is None


def test_log_messages_absent_from_package_all() -> None:
    """``__all__`` no longer advertises the class, and every name it lists resolves."""
    exported = list(logger_package.__all__)

    assert DEAD_SYMBOL not in exported

    unresolvable = [name for name in exported if not hasattr(logger_package, name)]
    assert not unresolvable, f"__all__ lists names the package does not define: {unresolvable}"


def test_log_messages_absent_from_shipped_data_flow_sources() -> None:
    """No file under the shipped ``slither/analyses/data_flow`` tree mentions the class.

    A source-level scan catches a reintroduction that the attribute checks would
    miss, such as the class being defined in a sibling module or referenced only
    from a docstring or comment.
    """
    package_root = Path(slither.analyses.data_flow.__file__).parent
    sources = sorted(package_root.rglob("*.py"))

    assert sources, f"expected Python sources under {package_root}"

    offenders = [
        str(path.relative_to(package_root))
        for path in sources
        if DEAD_SYMBOL in path.read_text(encoding="utf-8")
    ]

    assert not offenders, f"{DEAD_SYMBOL} reappeared under {package_root} in: {offenders}"
