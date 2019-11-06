
from slither.detectors.abstract_detector import AbstractDetector, DetectorClassification
from slither.slithir.operations import Nop


class VoidConstructor(AbstractDetector):

    ARGUMENT = 'void-cst'
    HELP = 'Constructor called not implemented'
    IMPACT = DetectorClassification.LOW
    CONFIDENCE = DetectorClassification.HIGH

    WIKI = 'https://github.com/crytic/slither/wiki/Detector-Documentation#void-constructor'

    WIKI_TITLE = 'Void Constructor'
    WIKI_DESCRIPTION = 'Detect the call to a constructor not implemented'
    WIKI_RECOMMENDATION = 'Remove the constructor call.'
    WIKI_EXPLOIT_SCENARIO = '''
```solidity
contract A{}
contract B is A{
    constructor() public A(){}
}
```
By reading B's constructor definition, the reader might assume that `A()` initiate the contract, while no code is executed.'''


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
                            info = "Void constructor called in {} ({}):\n"
                            info = info.format(cst.canonical_name, cst.source_mapping_str)
                            info += "\t-{} {}\n".format(str(node.expression), node.source_mapping_str)

                            json = self.generate_json_result(info)
                            self.add_function_to_json(cst, json)
                            self.add_nodes_to_json([node], json)
                            results.append(json)
        return results
