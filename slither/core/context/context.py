from collections import defaultdict
from typing import Dict


class Context:
    def __init__(self):
        super(Context, self).__init__()
        self._context = {"MEMBERS": defaultdict(None)}

    @property
    def context(self) -> Dict:
        """
        Dict used by analysis
        """
        return self._context
