from types import SimpleNamespace

from slither.printers.summary.human_summary import PrinterHumanSummary


def test_erc_order_is_stable():
    printer = object.__new__(PrinterHumanSummary)
    ercs = [f"ERC{index}" for index in range(32)]
    printer.contracts = [SimpleNamespace(ercs=lambda: ercs + ercs)]
    assert printer._ercs() == sorted(ercs)
