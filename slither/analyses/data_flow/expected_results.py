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
    "Assignment.sol": {
        "ArithmeticOverflowTests": {
            "test_addition_int16_overflow": {
                "variables": {
                    # No variables tracked
                }
            },
            "test_addition_int_checked": {
                "variables": {
                    # No variables tracked
                }
            },
            "test_addition_int_no_overflow": {
                "variables": {
                    "ArithmeticOverflowTests.test_addition_int_no_overflow().a|a_1": {"range": "[50, 50]", "overflow": "NO"},
                    "ArithmeticOverflowTests.test_addition_int_no_overflow().b|b_1": {"range": "[70, 70]", "overflow": "NO"},
                    "ArithmeticOverflowTests.test_addition_int_no_overflow().c|c_1": {"range": "[120, 120]", "overflow": "NO"},
                }
            },
            "test_addition_uint256_edge": {
                "variables": {
                    "ArithmeticOverflowTests.test_addition_uint256_edge().a|a_1": {"range": "[115792089237316195423570985008687907853269984665640564039457584007913129639925, 115792089237316195423570985008687907853269984665640564039457584007913129639925]", "overflow": "NO"},
                    "ArithmeticOverflowTests.test_addition_uint256_edge().b|b_1": {"range": "[5, 5]", "overflow": "NO"},
                    "ArithmeticOverflowTests.test_addition_uint256_edge().c|c_1": {"range": "[115792089237316195423570985008687907853269984665640564039457584007913129639930, 115792089237316195423570985008687907853269984665640564039457584007913129639930]", "overflow": "NO"},
                }
            },
            "test_addition_uint_overflow": {
                "variables": {
                    # No variables tracked
                }
            },
            "test_complex_expression_1": {
                "variables": {
                    # No variables tracked
                }
            },
            "test_complex_expression_2": {
                "variables": {
                    "ArithmeticOverflowTests.test_complex_expression_2().a|a_1": {"range": "[5, 5]", "overflow": "NO"},
                    "ArithmeticOverflowTests.test_complex_expression_2().b|b_1": {"range": "[10, 10]", "overflow": "NO"},
                    "ArithmeticOverflowTests.test_complex_expression_2().c|c_1": {"range": "[3, 3]", "overflow": "NO"},
                    "ArithmeticOverflowTests.test_complex_expression_2().result|result_1": {"range": "[45, 45]", "overflow": "NO"},
                }
            },
            "test_division_valid": {
                "variables": {
                    "ArithmeticOverflowTests.test_division_valid().a|a_1": {"range": "[1000, 1000]", "overflow": "NO"},
                    "ArithmeticOverflowTests.test_division_valid().b|b_1": {"range": "[7, 7]", "overflow": "NO"},
                    "ArithmeticOverflowTests.test_division_valid().c|c_1": {"range": "[142, 142]", "overflow": "NO"},
                }
            },
            "test_left_shift_overflow": {
                "variables": {
                    "ArithmeticOverflowTests.test_left_shift_overflow().a|a_1": {"range": "[1, 1]", "overflow": "NO"},
                    "ArithmeticOverflowTests.test_left_shift_overflow().b|b_1": {"range": "[0, 0]", "overflow": "NO"},
                }
            },
            "test_left_shift_valid": {
                "variables": {
                    "ArithmeticOverflowTests.test_left_shift_valid().a|a_1": {"range": "[1, 1]", "overflow": "NO"},
                    "ArithmeticOverflowTests.test_left_shift_valid().b|b_1": {"range": "[128, 128]", "overflow": "NO"},
                }
            },
            "test_max_value_increment": {
                "variables": {
                    # No variables tracked
                }
            },
            "test_modulo_valid": {
                "variables": {
                    "ArithmeticOverflowTests.test_modulo_valid().a|a_1": {"range": "[100, 100]", "overflow": "NO"},
                    "ArithmeticOverflowTests.test_modulo_valid().b|b_1": {"range": "[7, 7]", "overflow": "NO"},
                    "ArithmeticOverflowTests.test_modulo_valid().c|c_1": {"range": "[2, 2]", "overflow": "NO"},
                }
            },
            "test_multiple_uninitialized": {
                "variables": {
                    "ArithmeticOverflowTests.test_multiple_uninitialized().x": {"range": "[0, 0]", "overflow": "NO"},
                    "ArithmeticOverflowTests.test_multiple_uninitialized().x|x_0": {"range": "[0, 0]", "overflow": "NO"},
                    "ArithmeticOverflowTests.test_multiple_uninitialized().y": {"range": "[0, 0]", "overflow": "NO"},
                    "ArithmeticOverflowTests.test_multiple_uninitialized().y|y_0": {"range": "[0, 0]", "overflow": "NO"},
                    "ArithmeticOverflowTests.test_multiple_uninitialized().z|z_1": {"range": "[0, 0]", "overflow": "NO"},
                }
            },
            "test_multiplication_int_negative": {
                "variables": {
                    "ArithmeticOverflowTests.test_multiplication_int_negative().a|a_1": {"range": "[-10, -10]", "overflow": "NO"},
                    "ArithmeticOverflowTests.test_multiplication_int_negative().b|b_1": {"range": "[10, 10]", "overflow": "NO"},
                    "ArithmeticOverflowTests.test_multiplication_int_negative().c|c_1": {"range": "[-100, -100]", "overflow": "NO"},
                }
            },
            "test_multiplication_int_overflow": {
                "variables": {
                    # No variables tracked
                }
            },
            "test_multiplication_int_valid": {
                "variables": {
                    "ArithmeticOverflowTests.test_multiplication_int_valid().a|a_1": {"range": "[10, 10]", "overflow": "NO"},
                    "ArithmeticOverflowTests.test_multiplication_int_valid().b|b_1": {"range": "[12, 12]", "overflow": "NO"},
                    "ArithmeticOverflowTests.test_multiplication_int_valid().c|c_1": {"range": "[120, 120]", "overflow": "NO"},
                }
            },
            "test_multiplication_uint_overflow": {
                "variables": {
                    # No variables tracked
                }
            },
            "test_multiplication_uint_valid": {
                "variables": {
                    "ArithmeticOverflowTests.test_multiplication_uint_valid().a|a_1": {"range": "[15, 15]", "overflow": "NO"},
                    "ArithmeticOverflowTests.test_multiplication_uint_valid().b|b_1": {"range": "[17, 17]", "overflow": "NO"},
                    "ArithmeticOverflowTests.test_multiplication_uint_valid().c|c_1": {"range": "[255, 255]", "overflow": "NO"},
                }
            },
            "test_power_uint_overflow": {
                "variables": {
                    "ArithmeticOverflowTests.test_power_uint_overflow().a|a_1": {"range": "[2, 2]", "overflow": "NO"},
                    "ArithmeticOverflowTests.test_power_uint_overflow().b|b_1": {"range": "[0, 0]", "overflow": "NO"},
                    "ArithmeticOverflowTests.test_power_uint_overflow().c|c_1": {"range": "[8, 8]", "overflow": "NO"},
                }
            },
            "test_power_uint_valid": {
                "variables": {
                    "ArithmeticOverflowTests.test_power_uint_valid().a|a_1": {"range": "[2, 2]", "overflow": "NO"},
                    "ArithmeticOverflowTests.test_power_uint_valid().b|b_1": {"range": "[128, 128]", "overflow": "NO"},
                }
            },
            "test_power_zero_base": {
                "variables": {
                    "ArithmeticOverflowTests.test_power_zero_base().a|a_1": {"range": "[1, 1]", "overflow": "NO"},
                    "ArithmeticOverflowTests.test_power_zero_base().b|b_1": {"range": "[1, 1]", "overflow": "NO"},
                }
            },
            "test_power_zero_exponent": {
                "variables": {
                    "ArithmeticOverflowTests.test_power_zero_exponent().a|a_1": {"range": "[12345, 12345]", "overflow": "NO"},
                    "ArithmeticOverflowTests.test_power_zero_exponent().b|b_1": {"range": "[1, 1]", "overflow": "NO"},
                }
            },
            "test_right_shift": {
                "variables": {
                    "ArithmeticOverflowTests.test_right_shift().a|a_1": {"range": "[128, 128]", "overflow": "NO"},
                    "ArithmeticOverflowTests.test_right_shift().b|b_1": {"range": "[16, 16]", "overflow": "NO"},
                }
            },
            "test_subtraction_int_valid": {
                "variables": {
                    "ArithmeticOverflowTests.test_subtraction_int_valid().a|a_1": {"range": "[-100, -100]", "overflow": "NO"},
                    "ArithmeticOverflowTests.test_subtraction_int_valid().b|b_1": {"range": "[20, 20]", "overflow": "NO"},
                    "ArithmeticOverflowTests.test_subtraction_int_valid().c|c_1": {"range": "[-120, -120]", "overflow": "NO"},
                }
            },
            "test_subtraction_uint256_valid": {
                "variables": {
                    "ArithmeticOverflowTests.test_subtraction_uint256_valid().a|a_1": {"range": "[1000, 1000]", "overflow": "NO"},
                    "ArithmeticOverflowTests.test_subtraction_uint256_valid().b|b_1": {"range": "[300, 300]", "overflow": "NO"},
                    "ArithmeticOverflowTests.test_subtraction_uint256_valid().c|c_1": {"range": "[700, 700]", "overflow": "NO"},
                }
            },
            "test_subtraction_uint_underflow": {
                "variables": {
                    # No variables tracked
                }
            },
            "test_uint_max_increment": {
                "variables": {
                    # No variables tracked
                }
            },
            "test_uint_zero_decrement": {
                "variables": {
                    # No variables tracked
                }
            },
            "test_unchecked_addition_wraps": {
                "variables": {
                    "ArithmeticOverflowTests.test_unchecked_addition_wraps().a|a_1": {"range": "[200, 200]", "overflow": "NO"},
                    "ArithmeticOverflowTests.test_unchecked_addition_wraps().b|b_1": {"range": "[100, 100]", "overflow": "NO"},
                    "ArithmeticOverflowTests.test_unchecked_addition_wraps().c|c_1": {"range": "[44, 44]", "overflow": "YES"},
                }
            },
            "test_unchecked_multiplication_wraps": {
                "variables": {
                    "ArithmeticOverflowTests.test_unchecked_multiplication_wraps().a|a_1": {"range": "[20, 20]", "overflow": "NO"},
                    "ArithmeticOverflowTests.test_unchecked_multiplication_wraps().b|b_1": {"range": "[20, 20]", "overflow": "NO"},
                    "ArithmeticOverflowTests.test_unchecked_multiplication_wraps().c|c_1": {"range": "[144, 144]", "overflow": "YES"},
                }
            },
            "test_unchecked_subtraction_wraps": {
                "variables": {
                    "ArithmeticOverflowTests.test_unchecked_subtraction_wraps().a|a_1": {"range": "[50, 50]", "overflow": "NO"},
                    "ArithmeticOverflowTests.test_unchecked_subtraction_wraps().b|b_1": {"range": "[100, 100]", "overflow": "NO"},
                    "ArithmeticOverflowTests.test_unchecked_subtraction_wraps().c|c_1": {"range": "[206, 206]", "overflow": "YES"},
                }
            },
            "test_uninitialized_variable": {
                "variables": {
                    "ArithmeticOverflowTests.test_uninitialized_variable().a": {"range": "[0, 0]", "overflow": "NO"},
                    "ArithmeticOverflowTests.test_uninitialized_variable().a|a_0": {"range": "[0, 0]", "overflow": "NO"},
                    "ArithmeticOverflowTests.test_uninitialized_variable().b|b_1": {"range": "[10, 10]", "overflow": "NO"},
                }
            },
        },
    },
    "ByteExtractor.sol": {
        "ByteExtractor": {
            "getHardcodedByte": {
                "variables": {
                    "ByteExtractor.data|data_1": {"range": "[8234104122482341265491137074636836252947884782870784360943022469005013929455, 8234104122482341265491137074636836252947884782870784360943022469005013929455]", "overflow": "NO"},
                    "ByteExtractor.getHardcodedByte().firstByte|firstByte_1": {"range": "[18, 18]", "overflow": "NO"},
                }
            },
        },
    },
    "FunctionArgs.sol": {
        "FunctionArgsTests": {
            "callDouble": {
                "variables": {
                    "FunctionArgsTests.callDouble().arg|arg_1": {"range": "[10, 10]", "overflow": "NO"},
                    "FunctionArgsTests.callDouble().result|result_1": {"range": "[20, 20]", "overflow": "NO"},
                    "FunctionArgsTests.double(uint8).x|x_1": {"range": "[10, 10]", "overflow": "NO"},
                    "FunctionArgsTests.double(uint8).x|x_2": {"range": "[20, 20]", "overflow": "NO"},
                }
            },
            "complexExpression": {
                "variables": {
                    "FunctionArgsTests.complexExpression(uint256).x|x_1": {"range": "[1, 499]", "overflow": "NO"},
                    "FunctionArgsTests.complexExpression(uint256).y|y_1": {"range": "[2, 998]", "overflow": "NO"},
                }
            },
            "constrainedAdd": {
                "variables": {
                    "FunctionArgsTests.constrainedAdd(uint8,uint8).a|a_1": {"range": "[10, 100]", "overflow": "NO"},
                    "FunctionArgsTests.constrainedAdd(uint8,uint8).b|b_1": {"range": "[20, 50]", "overflow": "NO"},
                }
            },
            "double": {
                "variables": {
                    "FunctionArgsTests.double(uint8).x|x_1": {"range": "[0, 49]", "overflow": "NO"},
                    "FunctionArgsTests.double(uint8).x|x_2": {"range": "[0, 98]", "overflow": "NO"},
                }
            },
            "multipleCalls": {
                "variables": {
                    "FunctionArgsTests.constrainedAdd(uint8,uint8).a|a_1": {"range": "[30, 30]", "overflow": "NO"},
                    "FunctionArgsTests.constrainedAdd(uint8,uint8).b|b_1": {"range": "[25, 25]", "overflow": "NO"},
                    "FunctionArgsTests.double(uint8).x|x_1": {"range": "[25, 25]", "overflow": "NO"},
                    "FunctionArgsTests.double(uint8).x|x_2": {"range": "[50, 50]", "overflow": "NO"},
                    "FunctionArgsTests.multipleCalls().a|a_1": {"range": "[25, 25]", "overflow": "NO"},
                    "FunctionArgsTests.multipleCalls().b|b_1": {"range": "[50, 50]", "overflow": "NO"},
                    "FunctionArgsTests.multipleCalls().c|c_1": {"range": "[55, 55]", "overflow": "NO"},
                    "FunctionArgsTests.multipleCalls().d|d_1": {"range": "[105, 105]", "overflow": "NO"},
                }
            },
            "potentialOverflow": {
                "variables": {
                    # No variables tracked
                }
            },
            "potentialUnderflow": {
                "variables": {
                    # No variables tracked
                }
            },
        },
    },
    "Math.sol": {
        "MathOperations": {
            "addNoOverflow": {
                "variables": {
                    "MathOperations.addNoOverflow().a|a_1": {"range": "[100, 100]", "overflow": "NO"},
                    "MathOperations.addNoOverflow().b|b_1": {"range": "[50, 50]", "overflow": "NO"},
                    "MathOperations.addNoOverflow().c|c_1": {"range": "[150, 150]", "overflow": "NO"},
                }
            },
            "addWithOverflow": {
                "variables": {
                    # No variables tracked
                }
            },
            "complexExpression": {
                "variables": {
                    "MathOperations.complexExpression().a|a_1": {"range": "[10, 10]", "overflow": "NO"},
                    "MathOperations.complexExpression().b|b_1": {"range": "[20, 20]", "overflow": "NO"},
                    "MathOperations.complexExpression().c|c_1": {"range": "[60, 60]", "overflow": "NO"},
                    "MathOperations.complexExpression().d|d_1": {"range": "[50, 50]", "overflow": "NO"},
                    "MathOperations.complexExpression().e|e_1": {"range": "[10, 10]", "overflow": "NO"},
                }
            },
            "complexExpressionOverflow": {
                "variables": {
                    # No variables tracked
                }
            },
            "divideNumbers": {
                "variables": {
                    "MathOperations.divideNumbers().a|a_1": {"range": "[144, 144]", "overflow": "NO"},
                    "MathOperations.divideNumbers().b|b_1": {"range": "[12, 12]", "overflow": "NO"},
                    "MathOperations.divideNumbers().c|c_1": {"range": "[12, 12]", "overflow": "NO"},
                }
            },
            "exponentiationNoOverflow": {
                "variables": {
                    "MathOperations.exponentiationNoOverflow().base|base_1": {"range": "[2, 2]", "overflow": "NO"},
                    "MathOperations.exponentiationNoOverflow().result|result_1": {"range": "[128, 128]", "overflow": "NO"},
                }
            },
            "exponentiationOverflow": {
                "variables": {
                    "MathOperations.exponentiationOverflow().base|base_1": {"range": "[2, 2]", "overflow": "NO"},
                    "MathOperations.exponentiationOverflow().exp|exp_1": {"range": "[8, 8]", "overflow": "NO"},
                    "MathOperations.exponentiationOverflow().result|result_1": {"range": "[0, 0]", "overflow": "NO"},
                }
            },
            "leftShiftNoOverflow": {
                "variables": {
                    "MathOperations.leftShiftNoOverflow().a|a_1": {"range": "[1, 1]", "overflow": "NO"},
                    "MathOperations.leftShiftNoOverflow().b|b_1": {"range": "[128, 128]", "overflow": "NO"},
                }
            },
            "leftShiftOverflow": {
                "variables": {
                    "MathOperations.leftShiftOverflow().a|a_1": {"range": "[1, 1]", "overflow": "NO"},
                    "MathOperations.leftShiftOverflow().b|b_1": {"range": "[0, 0]", "overflow": "NO"},
                }
            },
            "mixedSignedUnsigned": {
                "variables": {
                    "MathOperations.mixedSignedUnsigned().a|a_1": {"range": "[50, 50]", "overflow": "NO"},
                    "MathOperations.mixedSignedUnsigned().b|b_1": {"range": "[100, 100]", "overflow": "NO"},
                    "MathOperations.mixedSignedUnsigned().c|c_1": {"range": "[150, 150]", "overflow": "NO"},
                }
            },
            "moduloOperation": {
                "variables": {
                    "MathOperations.moduloOperation().a|a_1": {"range": "[17, 17]", "overflow": "NO"},
                    "MathOperations.moduloOperation().b|b_1": {"range": "[5, 5]", "overflow": "NO"},
                    "MathOperations.moduloOperation().c|c_1": {"range": "[2, 2]", "overflow": "NO"},
                }
            },
            "multiplyNoOverflow": {
                "variables": {
                    "MathOperations.multiplyNoOverflow().a|a_1": {"range": "[15, 15]", "overflow": "NO"},
                    "MathOperations.multiplyNoOverflow().b|b_1": {"range": "[17, 17]", "overflow": "NO"},
                    "MathOperations.multiplyNoOverflow().c|c_1": {"range": "[255, 255]", "overflow": "NO"},
                }
            },
            "multiplyWithOverflow": {
                "variables": {
                    # No variables tracked
                }
            },
            "rightShift": {
                "variables": {
                    "MathOperations.rightShift().a|a_1": {"range": "[128, 128]", "overflow": "NO"},
                    "MathOperations.rightShift().b|b_1": {"range": "[16, 16]", "overflow": "NO"},
                }
            },
            "signedAdditionOverflow": {
                "variables": {
                    # No variables tracked
                }
            },
            "signedSubtractionUnderflow": {
                "variables": {
                    # No variables tracked
                }
            },
            "subtractNoUnderflow": {
                "variables": {
                    "MathOperations.subtractNoUnderflow().a|a_1": {"range": "[200, 200]", "overflow": "NO"},
                    "MathOperations.subtractNoUnderflow().b|b_1": {"range": "[50, 50]", "overflow": "NO"},
                    "MathOperations.subtractNoUnderflow().c|c_1": {"range": "[150, 150]", "overflow": "NO"},
                }
            },
            "subtractWithUnderflow": {
                "variables": {
                    # No variables tracked
                }
            },
            "uncheckedArithmetic": {
                "variables": {
                    "MathOperations.uncheckedArithmetic().a|a_1": {"range": "[200, 200]", "overflow": "NO"},
                    "MathOperations.uncheckedArithmetic().b|b_1": {"range": "[100, 100]", "overflow": "NO"},
                    "MathOperations.uncheckedArithmetic().c|c_1": {"range": "[44, 44]", "overflow": "YES"},
                }
            },
            "uninitializedVariable": {
                "variables": {
                    "MathOperations.uninitializedVariable().a": {"range": "[0, 0]", "overflow": "NO"},
                    "MathOperations.uninitializedVariable().a|a_0": {"range": "[0, 0]", "overflow": "NO"},
                    "MathOperations.uninitializedVariable().b|b_1": {"range": "[10, 10]", "overflow": "NO"},
                }
            },
        },
    },
    "Member.sol": {
        "SimpleMember": {
            "getBalance": {
                "variables": {
                    "REF_4": {"range": "[0, 115792089237316195423570985008687907853269984665640564039457584007913129639935]", "overflow": "NO"},
                    "SimpleMember.user|user_6.balance": {"range": "[0, 115792089237316195423570985008687907853269984665640564039457584007913129639935]", "overflow": "NO"},
                }
            },
            "getId": {
                "variables": {
                    "REF_2": {"range": "[1, 1]", "overflow": "NO"},
                    "REF_3": {"range": "[1, 1]", "overflow": "NO"},
                    "SimpleMember.user|user_4.id": {"range": "[1, 1]", "overflow": "NO"},
                    "SimpleMember.user|user_5.id": {"range": "[1, 1]", "overflow": "NO"},
                }
            },
            "setUser": {
                "variables": {
                    "REF_0": {"range": "[0, 9]", "overflow": "NO"},
                    "REF_1": {"range": "[0, 9]", "overflow": "NO"},
                    "SimpleMember.setUser(uint256,uint256)._balance|_balance_1": {"range": "[0, 9]", "overflow": "NO"},
                    "SimpleMember.setUser(uint256,uint256)._id|_id_1": {"range": "[0, 9]", "overflow": "NO"},
                    "SimpleMember.user|user_1.id": {"range": "[0, 9]", "overflow": "NO"},
                    "SimpleMember.user|user_2.balance": {"range": "[0, 9]", "overflow": "NO"},
                    "SimpleMember.user|user_2.id": {"range": "[0, 9]", "overflow": "NO"},
                    "SimpleMember.user|user_3.balance": {"range": "[0, 9]", "overflow": "NO"},
                    "SimpleMember.user|user_3.id": {"range": "[0, 9]", "overflow": "NO"},
                }
            },
        },
    },
    "Require.sol": {
        "RequireTests": {
            "requireAlwaysFalse": {
                "variables": {
                    # No variables tracked
                }
            },
            "requireComplexExpression": {
                "variables": {
                    # No variables tracked
                }
            },
            "requireExactValue": {
                "variables": {
                    # No variables tracked
                }
            },
            "requireLowerBound": {
                "variables": {
                    # No variables tracked
                }
            },
            "requireMultipleConstraints": {
                "variables": {
                    # No variables tracked
                }
            },
            "requireRange": {
                "variables": {
                    "RequireTests.requireRange().x|x_1": {"range": "[150, 150]", "overflow": "NO"},
                    "RequireTests.requireRange().y|y_1": {"range": "[300, 300]", "overflow": "NO"},
                }
            },
            "requireUpperBound": {
                "variables": {
                    # No variables tracked
                }
            },
        },
    },
    "Timestamp.sol": {
        "TimestampTests": {
            "timestampArithmetic": {
                "variables": {
                    "TimestampTests.timestampArithmetic().future|future_1": {"range": "[86400, 115792089237316195423570985008687907853269984665640564039457584007913129639935]", "overflow": "NO"},
                    "TimestampTests.timestampArithmetic().ts|ts_1": {"range": "[0, 115792089237316195423570985008687907853269984665640564039457584007913129553535]", "overflow": "NO"},
                    "block.timestamp": {"range": "[0, 115792089237316195423570985008687907853269984665640564039457584007913129553535]", "overflow": "NO"},
                }
            },
            "timestampAssignment": {
                "variables": {
                    "TimestampTests.timestampAssignment().ts|ts_1": {"range": "[0, 115792089237316195423570985008687907853269984665640564039457584007913129639935]", "overflow": "NO"},
                    "block.timestamp": {"range": "[0, 115792089237316195423570985008687907853269984665640564039457584007913129639935]", "overflow": "NO"},
                }
            },
        },
    },
    "Unary.sol": {
        "UnaryTests": {
            "bitwiseNotConstant": {
                "variables": {
                    "UnaryTests.bitwiseNotConstant().x|x_1": {"range": "[115792089237316195423570985008687907853269984665640564039457584007913129639935, 115792089237316195423570985008687907853269984665640564039457584007913129639935]", "overflow": "NO"},
                }
            },
            "bitwiseNotUint8": {
                "variables": {
                    "UnaryTests.bitwiseNotUint8(uint8).result|result_1": {"range": "[0, 255]", "overflow": "NO"},
                    "UnaryTests.bitwiseNotUint8(uint8).value|value_1": {"range": "[0, 255]", "overflow": "NO"},
                }
            },
            "bitwiseNotVariable": {
                "variables": {
                    "UnaryTests.bitwiseNotVariable(uint256).result|result_1": {"range": "[0, 115792089237316195423570985008687907853269984665640564039457584007913129639935]", "overflow": "NO"},
                    "UnaryTests.bitwiseNotVariable(uint256).value|value_1": {"range": "[0, 115792089237316195423570985008687907853269984665640564039457584007913129639935]", "overflow": "NO"},
                }
            },
            "complexUnary": {
                "variables": {
                    "UnaryTests.complexUnary(uint256,bool).a|a_1": {"range": "[1, 115792089237316195423570985008687907853269984665640564039457584007913129639935]", "overflow": "NO"},
                    "UnaryTests.complexUnary(uint256,bool).b|b_1": {"range": "[0, 1]", "overflow": "NO"},
                    "UnaryTests.complexUnary(uint256,bool).notA|notA_1": {"range": "[0, 115792089237316195423570985008687907853269984665640564039457584007913129639934]", "overflow": "NO"},
                    "UnaryTests.complexUnary(uint256,bool).notB|notB_1": {"range": "[0, 1]", "overflow": "NO"},
                    "UnaryTests.complexUnary(uint256,bool).result|result_1": {"range": "[0, 115792089237316195423570985008687907853269984665640564039457584007913129639934]", "overflow": "NO"},
                    "UnaryTests.complexUnary(uint256,bool).result|result_2": {"range": "[1, 115792089237316195423570985008687907853269984665640564039457584007913129639935]", "overflow": "NO"},
                    "UnaryTests.complexUnary(uint256,bool).result|result_3": {"range": "[0, 115792089237316195423570985008687907853269984665640564039457584007913129639935]", "overflow": "NO"},
                }
            },
            "logicalNotConstant": {
                "variables": {
                    "UnaryTests.logicalNotConstant().x|x_1": {"range": "[0, 0]", "overflow": "NO"},
                }
            },
            "logicalNotVariable": {
                "variables": {
                    "UnaryTests.logicalNotVariable(bool).result|result_1": {"range": "[0, 1]", "overflow": "NO"},
                    "UnaryTests.logicalNotVariable(bool).value|value_1": {"range": "[0, 1]", "overflow": "NO"},
                }
            },
        },
    },
}
