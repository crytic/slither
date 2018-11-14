import logging
from slither.core.slither_core import Slither

logger = logging.getLogger("VyperParsing")

class SlitherVyper(Slither):

    def __init__(self, filename):
        super(SlitherVyper, self).__init__()
        logger.info('Vyper parsing is not working yet {}'.format(filename))


