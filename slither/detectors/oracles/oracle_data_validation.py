from enum import Enum


from slither.detectors.abstract_detector import DetectorClassification
from slither.detectors.oracles.oracle_detector import Oracle, OracleDetector, VarInCondition






class OracleDataCheck(OracleDetector):
    """
    Documentation
    """

    ARGUMENT = "oracle-data-validation"  # slither will launch the detector with slither.py --detect mydetector
    HELP = "Oracle vulnerabilities"
    IMPACT = DetectorClassification.MEDIUM
    CONFIDENCE = DetectorClassification.MEDIUM

    WIKI = "https://github.com/crytic/slither/wiki/Detector-Documentation#oracle-data-validation"

    WIKI_TITLE = "Oracle data validation"
    WIKI_DESCRIPTION = "The detection of not correct validation of oracle data."
    WIKI_EXPLOIT_SCENARIO = "---"
    WIKI_RECOMMENDATION = "Validate the data returned by the oracle. For more information visit https://docs.chain.link/data-feeds/api-reference"



    # This function is necessary even though there is a detector for unused return values because the variable can be used but will not be validated in conditional statements
    def process_not_checked_vars(self):
        result = []
        for oracle in self.oracles:
            if len(oracle.vars_not_in_condition) > 0:
                result.append(
                    f"The oracle {oracle.contract}.{oracle.interface} ({oracle.node.source_mapping}) returns the variables {[var.name for var in oracle.vars_not_in_condition]} which are not validated. It can potentially lead to unexpected behaviour.\n"
                )
        return result

    def _detect(self):
        results = []
        super()._detect()
        not_checked_vars = self.process_not_checked_vars()
        if len(not_checked_vars) > 0:
            res = self.generate_result(not_checked_vars)
            results.append(res)
        for oracle in self.oracles:
            checked_vars = oracle.naive_data_validation()
            if len(checked_vars) > 0:
                res = self.generate_result(checked_vars)
                results.append(res)
        return results
