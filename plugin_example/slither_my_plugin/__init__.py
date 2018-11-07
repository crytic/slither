from slither_my_plugin.detectors.example import Example


def make_plugin():
    plugin_detectors = [Example]
    plugin_printers = []

    return plugin_detectors, plugin_printers
