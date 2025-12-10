"""Expected results for automated data flow analysis tests.

Format: contract_file -> contract_name -> function_name -> variables
Each variable has: range (as "[min, max]"), overflow ("YES"/"NO")
"""

from typing import Dict

EXPECTED_RESULTS: Dict[str, Dict[str, Dict[str, Dict[str, Dict]]]] = {
    "Addition.sol": {
        "Addition": {
            "add": {
                "variables": {
                    "Addition.add().foo|foo_1": {"range": "[7, 7]", "overflow": "NO"},
                    "Addition.add().number|number_1": {"range": "[200, 200]", "overflow": "NO"},
                    "Addition.add().result|result_1": {"range": "[207, 207]", "overflow": "NO"},
                }
            },
            "add2": {
                "variables": {
                    "Addition.add2().a|a_1": {"range": "[65530, 65530]", "overflow": "NO"},
                    "Addition.add2().foo|foo_1": {"range": "[10, 10]", "overflow": "NO"},
                    "Addition.add2().number|number_1": {"range": "[65520, 65520]", "overflow": "NO"},
                    "Addition.add2().result|result_1": {"range": "[65530, 65530]", "overflow": "NO"},
                }
            },
            "add3": {
                "variables": {
                    "Addition.add3().a": {"range": "[0, 0]", "overflow": "NO"},
                    "Addition.add3().a|a_0": {"range": "[0, 0]", "overflow": "NO"},
                    "Addition.add3().a|a_1": {"range": "[-10, -10]", "overflow": "NO"},
                }
            },
            "substract": {
                "variables": {
                    "Addition.substract().add|add_1": {"range": "[155, 155]", "overflow": "NO"},
                    "Addition.substract().foo|foo_1": {"range": "[255, 255]", "overflow": "NO"},
                    "Addition.substract().number|number_1": {"range": "[100, 100]", "overflow": "NO"},
                    "Addition.substract().zero|zero_1": {"range": "[0, 0]", "overflow": "NO"},
                }
            },
        },
    },
    "Assert.sol": {
        "SimpleAssert": {
            "checkMath": {
                "variables": {
                    "SimpleAssert.checkMath().x|x_1": {"range": "[5, 5]", "overflow": "NO"},
                    "SimpleAssert.checkMath().y|y_1": {"range": "[15, 15]", "overflow": "NO"},
                    "SimpleAssert.checkMath().y|y_2": {"range": "[16, 16]", "overflow": "NO"},
                }
            },
        },
    },
    "Assignment.sol": {
        "ArithmeticOverflowTests": {
            "test_unchecked_addition_wraps": {
                "variables": {
                    "ArithmeticOverflowTests.test_unchecked_addition_wraps().a|a_1": {"range": "[200, 200]", "overflow": "NO"},
                    "ArithmeticOverflowTests.test_unchecked_addition_wraps().b|b_1": {"range": "[100, 100]", "overflow": "NO"},
                    "ArithmeticOverflowTests.test_unchecked_addition_wraps().c|c_1": {"range": "[44, 44]", "overflow": "YES"},
                }
            },
        },
    },
    "Counter.sol": {
        "Counter": {
            "setNumber": {
                "variables": {
                    "Counter.number|number_1": {"range": "[0, 115792089237316195423570985008687907853269984665640564039457584007913129639935]", "overflow": "NO"},
                    "Counter.setNumber(uint256).newNumber|newNumber_1": {"range": "[0, 115792089237316195423570985008687907853269984665640564039457584007913129639935]", "overflow": "NO"},
                }
            },
        },
    },
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
                    "SimpleFunction.double(uint8).x|x_1": {"range": "[10, 10]", "overflow": "NO"},
                    "SimpleFunction.double(uint8).x|x_2": {"range": "[20, 20]", "overflow": "NO"},
                    "SimpleFunction.foo().arg|arg_1": {"range": "[10, 10]", "overflow": "NO"},
                    "SimpleFunction.foo().result|result_1": {"range": "[20, 20]", "overflow": "NO"},
                }
            },
        },
    },
    "Math.sol": {
        "MathOperations": {
            "bitwiseAnd": {
                "variables": {
                    "MathOperations.bitwiseAnd().l|l_1": {"range": "[8, 8]", "overflow": "NO"},
                }
            },
        },
    },
    "Require.sol": {
        "RequireContract": {
            "checkRange": {
                "variables": {
                    # No variables tracked
                }
            },
        },
    },
    "SimpleAddress.sol": {
        "SimpleAddressContract": {
            "getAddress": {
                "variables": {
                    "SimpleAddressContract.getAddress().myAddress|myAddress_1": {"range": "[520786028573371803640530888255888666801131675076, 520786028573371803640530888255888666801131675076]", "overflow": "NO"},
                }
            },
            "getCallerAddress": {
                "variables": {
                    "SimpleAddressContract.getCallerAddress().caller|caller_1": {"range": "[0, 1461501637330902918203684832716283019655932542975]", "overflow": "NO"},
                    "msg.sender": {"range": "[0, 1461501637330902918203684832716283019655932542975]", "overflow": "NO"},
                }
            },
            "getZeroAddress": {
                "variables": {
                    "SimpleAddressContract.getZeroAddress().zero|zero_1": {"range": "[0, 0]", "overflow": "NO"},
                }
            },
        },
    },
    "Test.sol": {
        "TestContract": {
            "test": {
                "variables": {
                    "TestContract.test().test": {"range": "[0, 0]", "overflow": "NO"},
                    "TestContract.test().test|test_0": {"range": "[0, 0]", "overflow": "NO"},
                    "TestContract.test().test|test_1": {"range": "[10, 10]", "overflow": "NO"},
                    "TestContract.test().test|test_2": {"range": "[5, 5]", "overflow": "NO"},
                    "TestContract.test().test|test_3": {"range": "[10, 10]", "overflow": "NO"},
                    "TestContract.test().test|test_4": {"range": "[11, 11]", "overflow": "NO"},
                }
            },
        },
    },
}
