import re
from slither.detectors.abstract_detector import AbstractDetector, DetectorClassification


class KValueError(AbstractDetector):
    """
    Module detecting multiple constructors in the same contract.
    (This was possible prior to Solidity 0.4.23, using old and new constructor schemes).
    """

    ARGUMENT = "k-value-error"
    HELP = "Multiple constructor schemes"
    IMPACT = DetectorClassification.HIGH
    CONFIDENCE = DetectorClassification.HIGH

    WIKI = " "

    WIKI_TITLE = "Multiple constructor schemes"
    WIKI_DESCRIPTION = (
        "Detect multiple constructor definitions in the same contract (using new and old schemes)."
    )

    # region wiki_exploit_scenario
    WIKI_EXPLOIT_SCENARIO = """"""
    WIKI_RECOMMENDATION = "Only declare one constructor, preferably using the new scheme `constructor(...)` instead of `function <contractName>(...)`."

    def _detect(self):
        """
        Detect multiple constructor schemes in the same contract
        :return: Returns a list of contract JSON result, where each result contains all constructor definitions.
        """
        results = []
        matches0=""
        matches1=""
        matches2=""
        tainted_function_name=""
        tainted_nodes=[]
        
        for contract in self.contracts:
            # check if uniswap
            if "pair" in contract.name.lower() and any("swap" == f.name for f in contract.functions) and any("burn" == f.name for f in contract.functions) and any("mint" == f.name for f in contract.functions):
                print("found function")
                for f in contract.functions:
                    if f.name=="swap":
                        print("found swap")
                        tainted_function_name=f.name
                        for node in f.nodes:
                            pattern = r'10+'
                            if "balance0.mul(" in str(node):
                                matches0 = re.findall(pattern, str(node))
                                tainted_nodes.append(node)
                            if "balance1.mul(" in str(node):
                                matches1 = re.findall(pattern, str(node))
                                tainted_nodes.append(node)
                            if "require" in str(node) and ">=" in str(node):
                                matches2 = re.findall(pattern, str(node))
                                tainted_nodes.append(node)
        if matches2!=matches0 or matches2!=matches1:
            info = [tainted_function_name, " has potential K Value Error in :\n",tainted_nodes[0],tainted_nodes[1],tainted_nodes[2]]
            res = self.generate_result(info)
            results.append(res)

        return results
