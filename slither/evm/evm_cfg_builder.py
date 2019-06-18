import logging
import sys

logger = logging.getLogger('ConvertToEVM')

def load_evm_cfg_builder():
    try:
        # Avoiding the addition of evm_cfg_builder as permanent dependency
        from evm_cfg_builder.cfg import CFG
        return CFG
    except ImportError:
        logger.error("To use evm features, you need to install evm-cfg-builder from Trail of Bits")
        logger.error("Documentation: https://github.com/crytic/evm_cfg_builder")
        logger.error("Installation: pip install evm-cfg-builder")
        sys.exit(-1)