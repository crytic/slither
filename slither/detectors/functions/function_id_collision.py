
from slither.detectors.abstract_detector import (AbstractDetector,
                                                 DetectorClassification)

from slither.utils.function import get_function_id


class FunctionIDCollision(AbstractDetector):
    """
    """

    ARGUMENT = 'function-id'
    HELP = 'Functions IDs collision'
    IMPACT = DetectorClassification.HIGH
    CONFIDENCE = DetectorClassification.HIGH

    WIKI = 'todo'

    WIKI_TITLE = 'Functions IDS collision'
    WIKI_DESCRIPTION = 'Functions sharing the same signature.'
    WIKI_EXPLOIT_SCENARIO = '''
```python
public
@constant
def gsf() -> uint256:
    return 1

@public
@constant
def tgeo()  -> uint256:
    return 2
```
Both functions have 0x67e43e43 as function id. As a result, calling tgeo() will return 1 instead of 2.'''

    WIKI_RECOMMENDATION = 'Change the function signature.'

    def _detect_id_collision(self, c):
        sigs = {}
        for function in c.functions_entry_points:
            sig = get_function_id(function.full_name)
            if not sig in sigs:
                sigs[sig] = []
            sigs[sig].append(function)

        return [c for c in sigs.values() if len(c)>1]


    def _detect(self):
        """
        """
        results = []

        for c in self.contracts:
            colissions = self._detect_id_collision(c)
            for colission in colissions:

                info = f"Functions collision found {hex(get_function_id(colission[0].full_name))}:\n"
                for function in colission:
                    info += '\t- {} ({})\n'.format(function.full_name, function.source_mapping_str)

                json = self.generate_json_result(info)
                for function in colission:
                    self.add_function_to_json(function, json)
                results.append(json)

        return results
