import logging
from slither.exceptions import SlitherError

logger = logging.getLogger("ConvertToEVM")


def load_evm_cfg_builder():
    try:
        # Avoiding the addition of evm_cfg_builder as permanent dependency
        # pylint: disable=import-outside-toplevel
        from evm_cfg_builder.cfg import CFG

        return CFG
    except ImportError:
        logger.error("To use evm features, you need to install evm-cfg-builder")
        logger.error("Documentation: https://github.com/crytic/evm_cfg_builder")
        logger.error("Installation: pip install evm-cfg-builder")
        raise SlitherError("evm-cfg-builder not installed.")
