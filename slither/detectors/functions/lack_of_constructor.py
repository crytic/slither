from slither.detectors.abstract_detector import AbstractDetector, DetectorClassification

class MissingConstructor(AbstractDetector):
    """base on Jiuzhou dataset"""
    ARGUMENT = "missing-contructor"
    HELP = "Null"
    IMPACT = DetectorClassification.INFORMATIONAL
    CONFIDENCE = DetectorClassification.HIGH

    WIKI = "https://github.com/crytic/slither/wiki/Detector-Documentation/#missing-contructor"
    WIKI_TITLE = "Missing constructor"
    WIKI_DESCRIPTION = "In some cases, the lack of constructors can be dangerous. If the developer is not going to write a constructor for the contract, the harm of the lack of a constructor is limited to the structural incompleteness of the contract. If the developer intends to write a constructor for the contract, but misspells the function name due to the developer's own negligence, the contract is at great risk. Because in contracts, constructors are often tasked with assigning values to key state variables."

    # region wiki_exploit_scenario
    WIKI_EXPLOIT_SCENARIO = """"""
    # endregion wiki_exploit_scenario

    WIKI_RECOMMENDATION = "add a contructor."

    def _detect(self):
        """"""
        res = []
        results = []

        for c in self.contracts:
            constructor = False

            for f in c.functions_declared:
                if f.is_constructor:
                    constructor = True
                    break

            if not constructor:
                info = [c, " is missing a constructor.\n",]
                res = self.generate_result(info)
                results.append(res)

        return results