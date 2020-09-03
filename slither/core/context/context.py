from collections import defaultdict
from typing import Dict


class Context:  # pylint: disable=too-few-public-methods
    def __init__(self):
        super().__init__()
        self._context = {"MEMBERS": defaultdict(None)}

    @property
    def context(self) -> Dict:
        """
        Dict used by analysis
        """
        return self._context
