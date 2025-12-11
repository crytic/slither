"""Expected results for automated data flow analysis tests.

Format: contract_file -> contract_name -> function_name -> variables
Each variable has: range (as "[min, max]"), overflow ("YES"/"NO")
"""

from typing import Dict

EXPECTED_RESULTS: Dict[str, Dict[str, Dict[str, Dict[str, Dict]]]] = {
    "Assert.sol": {
        "AssertTests": {
            "assertAlwaysFalse": {
                "variables": {
                    # No variables tracked
                }
            },
            "assertExactValue": {
                "variables": {
                    "AssertTests.assertExactValue().x|x_1": {"range": "[5, 5]", "overflow": "NO"},
                    "AssertTests.assertExactValue().y|y_1": {"range": "[15, 15]", "overflow": "NO"},
                    "AssertTests.assertExactValue().z|z_1": {"range": "[16, 16]", "overflow": "NO"},
                }
            },
            "assertMultipleConstraints": {
                "variables": {
                    "AssertTests.assertMultipleConstraints().result|result_1": {"range": "[160, 160]", "overflow": "NO"},
                    "AssertTests.assertMultipleConstraints().value|value_1": {"range": "[100, 100]", "overflow": "NO"},
                    "AssertTests.assertMultipleConstraints().value|value_2": {"range": "[150, 150]", "overflow": "NO"},
                }
            },
            "assertRangeNarrowing": {
                "variables": {
                    "AssertTests.assertRangeNarrowing().a|a_1": {"range": "[100, 100]", "overflow": "NO"},
                    "AssertTests.assertRangeNarrowing().b|b_1": {"range": "[150, 150]", "overflow": "NO"},
                    "AssertTests.assertRangeNarrowing().c|c_1": {"range": "[160, 160]", "overflow": "NO"},
                }
            },
            "assertSignedRange": {
                "variables": {
                    "AssertTests.assertSignedRange().x|x_1": {"range": "[50, 50]", "overflow": "NO"},
                    "AssertTests.assertSignedRange().y|y_1": {"range": "[20, 20]", "overflow": "NO"},
                    "AssertTests.assertSignedRange().z|z_1": {"range": "[40, 40]", "overflow": "NO"},
                }
            },
        },
    },
}
