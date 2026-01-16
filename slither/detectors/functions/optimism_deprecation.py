from slither.detectors.abstract_detector import (
    AbstractDetector,
    DetectorClassification,
    DETECTOR_INFO,
)
from slither.core.cfg.node import Node
from slither.core.variables.variable import Variable
from slither.core.expressions import TypeConversion, Literal
from slither.utils.output import Output


class OptimismDeprecation(AbstractDetector):
    ARGUMENT = "optimism-deprecation"
    HELP = "Detect when deprecated Optimism predeploy or function is used."
    IMPACT = DetectorClassification.LOW
    CONFIDENCE = DetectorClassification.HIGH

    WIKI = "https://github.com/crytic/slither/wiki/Detector-Documentation#optimism-deprecated-predeploy-or-function"

    WIKI_TITLE = "Optimism deprecated predeploy or function"
    WIKI_DESCRIPTION = "Detect when deprecated Optimism predeploy or function is used."

    # region wiki_exploit_scenario
    WIKI_EXPLOIT_SCENARIO = """
```solidity
interface GasPriceOracle {
    function scalar() external view returns (uint256);
}

contract Test {
    GasPriceOracle constant OPT_GAS = GasPriceOracle(0x420000000000000000000000000000000000000F);

    function a() public {
        OPT_GAS.scalar();
    }
}
```
The call to the `scalar` function of the Optimism GasPriceOracle predeploy always revert.
"""
    # endregion wiki_exploit_scenario

    WIKI_RECOMMENDATION = "Do not use the deprecated components."

    def _detect(self) -> list[Output]:
        results = []

        deprecated_predeploys = [
            "0x4200000000000000000000000000000000000000",  # LegacyMessagePasser
            "0x4200000000000000000000000000000000000001",  # L1MessageSender
            "0x4200000000000000000000000000000000000002",  # DeployerWhitelist
            "0x4200000000000000000000000000000000000013",  # L1BlockNumber
        ]

        for contract in self.compilation_unit.contracts_derived:
            use_deprecated: list[Node] = []

            for _, ir in contract.all_high_level_calls:
                # To avoid FPs we assume predeploy contracts are always assigned to a constant and typecasted to an interface
                # and we check the target address of a high level call.
                if (
                    isinstance(ir.destination, Variable)
                    and isinstance(ir.destination.expression, TypeConversion)
                    and isinstance(ir.destination.expression.expression, Literal)
                ):
                    if ir.destination.expression.expression.value in deprecated_predeploys:
                        use_deprecated.append(ir.node)

                    if (
                        ir.destination.expression.expression.value
                        == "0x420000000000000000000000000000000000000F"
                        and ir.function_name in ("overhead", "scalar", "getL1GasUsed")
                    ):
                        use_deprecated.append(ir.node)
            # Sort so output is deterministic
            use_deprecated.sort(key=lambda x: (x.node_id, x.function.full_name))
            if len(use_deprecated) > 0:
                info: DETECTOR_INFO = [
                    "A deprecated Optimism predeploy or function is used in the ",
                    contract.name,
                    " contract.\n",
                ]

                for node in use_deprecated:
                    info.extend(["\t - ", node, "\n"])

                res = self.generate_result(info)
                results.append(res)

        return results
