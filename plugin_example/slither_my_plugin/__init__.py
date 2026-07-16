from slither_my_plugin.detectors.example import Example

from slither.detectors.abstract_detector import AbstractDetector
from slither.printers.abstract_printer import AbstractPrinter


def make_plugin() -> tuple[list[type[AbstractDetector]], list[type[AbstractPrinter]]]:
    plugin_detectors = [Example]
    plugin_printers: list[type[AbstractPrinter]] = []

    return plugin_detectors, plugin_printers
