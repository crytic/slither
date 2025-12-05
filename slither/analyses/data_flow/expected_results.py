"""Expected results for automated data flow analysis tests.

Format: contract_file -> contract_name -> function_name -> variables
Each variable has: range (as "[min, max]"), overflow ("YES"/"NO")
"""

from typing import Dict

EXPECTED_RESULTS: Dict[str, Dict[str, Dict[str, Dict[str, Dict[str, str]]]]] = {
    "FunctionArgs.sol": {
        "SimpleFunction": {
            "double": {
                "variables": {
                    "SimpleFunction.double(uint8).x|x_1": {"range": "[0, 49]", "overflow": "NO"},
                    "SimpleFunction.double(uint8).x|x_2": {"range": "[0, 98]", "overflow": "NO"},
                }
            },
            "foo": {
                "variables": {
                    "SimpleFunction.foo().arg|arg_1": {"range": "[10, 10]", "overflow": "NO"},
                    "SimpleFunction.foo().result|result_1": {"range": "[20, 20]", "overflow": "NO"},
                    "SimpleFunction.double(uint8).x|x_1": {"range": "[10, 10]", "overflow": "NO"},
                    "SimpleFunction.double(uint8).x|x_2": {"range": "[20, 20]", "overflow": "NO"},
                }
            },
        }
    },
    "Addition.sol": {
        "Addition": {
            "add": {
                "variables": {
                    "Addition.add().number|number_1": {"range": "[200, 200]", "overflow": "NO"},
                    "Addition.add().foo|foo_1": {"range": "[7, 7]", "overflow": "NO"},
                    "Addition.add().result|result_1": {"range": "[207, 207]", "overflow": "NO"},
                }
            },
            "add2": {
                "variables": {
                    "Addition.add2().number|number_1": {
                        "range": "[65520, 65520]",
                        "overflow": "NO",
                    },
                    "Addition.add2().foo|foo_1": {"range": "[10, 10]", "overflow": "NO"},
                    "Addition.add2().result|result_1": {
                        "range": "[65530, 65530]",
                        "overflow": "NO",
                    },
                    "Addition.add2().a|a_1": {"range": "[65530, 65530]", "overflow": "NO"},
                }
            },
            "substract": {
                "variables": {
                    "Addition.substract().number|number_1": {
                        "range": "[100, 100]",
                        "overflow": "NO",
                    },
                    "Addition.substract().foo|foo_1": {"range": "[255, 255]", "overflow": "NO"},
                    "Addition.substract().zero|zero_1": {"range": "[0, 0]", "overflow": "NO"},
                    "Addition.substract().add|add_1": {"range": "[155, 155]", "overflow": "NO"},
                }
            },
            "add3": {
                "variables": {
                    "Addition.add3().a|a_1": {"range": "[-10, -10]", "overflow": "NO"},
                }
            },
        }
    },
    "Assert.sol": {
        "SimpleAssert": {
            "checkMath": {
                "variables": {
                    "SimpleAssert.checkMath().x|x_1": {"range": "[5, 5]", "overflow": "NO"},
                    "SimpleAssert.checkMath().y|y_2": {"range": "[16, 16]", "overflow": "NO"},
                }
            }
        }
    },
    "Assignment.sol": {
        "ArithmeticOverflowTests": {
            "test_unchecked_addition_wraps": {
                "variables": {
                    "ArithmeticOverflowTests.test_unchecked_addition_wraps().a|a_1": {
                        "range": "[200, 200]",
                        "overflow": "NO",
                    },
                    "ArithmeticOverflowTests.test_unchecked_addition_wraps().b|b_1": {
                        "range": "[100, 100]",
                        "overflow": "NO",
                    },
                    "ArithmeticOverflowTests.test_unchecked_addition_wraps().c|c_1": {
                        "range": "[44, 44]",
                        "overflow": "YES",
                    },
                }
            }
        }
    },
    "Counter.sol": {
        "Counter": {
            "setNumber": {
                "variables": {}  # State variable assignment, may not produce tracked vars
            },
            "increment": {
                "variables": {}  # State variable increment, may not produce tracked vars
            },
        }
    },
    # Note: Math.sol bitwise operations currently return full type range (analysis limitation)
    # Note: Require.sol constraint propagation not fully working (analysis limitation)
}
