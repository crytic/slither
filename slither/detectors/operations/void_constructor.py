
from slither.detectors.abstract_detector import AbstractDetector, DetectorClassification
from slither.slithir.operations import Nop


class VoidConstructor(AbstractDetector):

    ARGUMENT = 'void-cst'
    HELP = 'Constructor called not implemented'
    IMPACT = DetectorClassification.LOW
    CONFIDENCE = DetectorClassification.HIGH

    WIKI = 'https://github.com/crytic/slither/wiki/Detector-Documentation#void-constructor'

    WIKI_TITLE = 'Void constructor'
    WIKI_DESCRIPTION = 'Detect the call to a constructor that is not implemented'
    WIKI_RECOMMENDATION = 'Remove the constructor call.'
    WIKI_EXPLOIT_SCENARIO = '''
```solidity
contract A{}
contract B is A{
    constructor() public A(){}
}
```
When reading `B`'s constructor definition, we might assume that `A()` initiates the contract, but no code is executed.'''


    def _detect(self):
        """
        """
        results = []
        for c in self.contracts:
            cst = c.constructor
            if cst:

                for constructor_call in cst.explicit_base_constructor_calls_statements:
                    for node in constructor_call.nodes:
                        if any(isinstance(ir, Nop) for ir in node.irs):
                            info = ["Void constructor called in ", cst, ":\n"]
                            info += ["\t- ", node, "\n"]

                            res = self.generate_result(info)

                            results.append(res)
        return results
