from typing import List, Set

from slither.core.cfg.node import Node, NodeType
from slither.core.declarations import Function
from slither.core.expressions import BinaryOperation, Identifier, MemberAccess, UnaryOperation
from slither.core.solidity_types import ArrayType
from slither.core.variables import StateVariable
from slither.detectors.abstract_detector import AbstractDetector, DetectorClassification
from slither.slithir.operations import Length, Delete, HighLevelCall


class CacheArrayLength(AbstractDetector):
    """
    Detects `for` loops that use `length` member of some storage array in their loop condition and don't modify it.
    """

    ARGUMENT = "cache-array-length"
    HELP = (
        "Detects `for` loops that use `length` member of some storage array in their loop condition and don't "
        "modify it."
    )
    IMPACT = DetectorClassification.OPTIMIZATION
    CONFIDENCE = DetectorClassification.HIGH

    WIKI = "https://github.com/crytic/slither/wiki/Detector-Documentation#cache-array-length"

    WIKI_TITLE = "Cache array length"
    WIKI_DESCRIPTION = (
        "Detects `for` loops that use `length` member of some storage array in their loop condition "
        "and don't modify it. "
    )
    WIKI_EXPLOIT_SCENARIO = """
```solidity
contract C
{
    uint[] array;
    
    function f() public 
    {
        for (uint i = 0; i < array.length; i++)
        {
            // code that does not modify length of `array`
        }
    }
}
```
Since the `for` loop in `f` doesn't modify `array.length`, it is more gas efficient to cache it in some local variable and use that variable instead, like in the following example:

```solidity
contract C
{
    uint[] array;
    
    function f() public 
    {
        uint array_length = array.length;
        for (uint i = 0; i < array_length; i++)
        {
            // code that does not modify length of `array`
        }
    }
}
```
    """
    WIKI_RECOMMENDATION = (
        "Cache the lengths of storage arrays if they are used and not modified in `for` loops."
    )

    @staticmethod
    def _is_identifier_member_access_comparison(exp: BinaryOperation) -> bool:
        """
        Checks whether a BinaryOperation `exp` is an operation on Identifier and MemberAccess.
        """
        return (
            isinstance(exp.expression_left, Identifier)
            and isinstance(exp.expression_right, MemberAccess)
        ) or (
            isinstance(exp.expression_left, MemberAccess)
            and isinstance(exp.expression_right, Identifier)
        )

    @staticmethod
    def _extract_array_from_length_member_access(exp: MemberAccess) -> StateVariable:
        """
        Given a member access `exp`, it returns state array which `length` member is accessed through `exp`.
        If array is not a state array or its `length` member is not referenced, it returns `None`.
        """
        if exp.member_name != "length":
            return None
        if not isinstance(exp.expression, Identifier):
            return None
        if not isinstance(exp.expression.value, StateVariable):
            return None
        if not isinstance(exp.expression.value.type, ArrayType):
            return None
        return exp.expression.value

    @staticmethod
    def _is_loop_referencing_array_length(
        node: Node, visited: Set[Node], array: StateVariable, depth: int
    ) -> True:
        """
        For a given loop, checks if it references `array.length` at some point.
        Will also return True if `array.length` is referenced but not changed.
        This may potentially generate false negatives in the detector, but it was done this way because:
        - situations when array `length` is referenced but not modified in loop are rare
        - checking if `array.length` is indeed modified would require much more work
        """
        visited.add(node)
        if node.type == NodeType.STARTLOOP:
            depth += 1
        if node.type == NodeType.ENDLOOP:
            depth -= 1
        if depth == 0:
            return False

        # Array length may change in the following situations:
        # - when `push` is called
        # - when `pop` is called
        # - when `delete` is called on the entire array
        # - when external function call is made (instructions from internal function calls are already in
        #   `node.all_slithir_operations()`, so we don't need to handle internal calls separately)
        if node.type == NodeType.EXPRESSION:
            for op in node.all_slithir_operations():
                if isinstance(op, Length) and op.value == array:
                    # op accesses array.length, not necessarily modifying it
                    return True
                if isinstance(op, Delete):
                    # take into account only delete entire array, since delete array[i] doesn't change `array.length`
                    if (
                        isinstance(op.expression, UnaryOperation)
                        and isinstance(op.expression.expression, Identifier)
                        and op.expression.expression.value == array
                    ):
                        return True
                if (
                    isinstance(op, HighLevelCall)
                    and isinstance(op.function, Function)
                    and not op.function.view
                    and not op.function.pure
                ):
                    return True

        for son in node.sons:
            if son not in visited:
                if CacheArrayLength._is_loop_referencing_array_length(son, visited, array, depth):
                    return True
        return False

    @staticmethod
    def _handle_loops(nodes: List[Node], non_optimal_array_len_usages: List[Node]) -> None:
        """
        For each loop, checks if it has a comparison with `length` array member and, if it has, checks whether that
        array size could potentially change in that loop.
        If it cannot, the loop condition is added to `non_optimal_array_len_usages`.
        There may be some false negatives here - see docs for `_is_loop_referencing_array_length` for more information.
        """
        for node in nodes:
            if node.type == NodeType.STARTLOOP:
                if_node = node.sons[0]
                if if_node.type != NodeType.IFLOOP:
                    continue
                if not isinstance(if_node.expression, BinaryOperation):
                    continue
                exp: BinaryOperation = if_node.expression
                if not CacheArrayLength._is_identifier_member_access_comparison(exp):
                    continue
                array: StateVariable
                if isinstance(exp.expression_right, MemberAccess):
                    array = CacheArrayLength._extract_array_from_length_member_access(
                        exp.expression_right
                    )
                else:  # isinstance(exp.expression_left, MemberAccess) == True
                    array = CacheArrayLength._extract_array_from_length_member_access(
                        exp.expression_left
                    )
                if array is None:
                    continue

                visited: Set[Node] = set()
                if not CacheArrayLength._is_loop_referencing_array_length(
                    if_node, visited, array, 1
                ):
                    non_optimal_array_len_usages.append(if_node)

    @staticmethod
    def _get_non_optimal_array_len_usages_for_function(f: Function) -> List[Node]:
        """
        Finds non-optimal usages of array length in loop conditions in a given function.
        """
        non_optimal_array_len_usages: List[Node] = []
        CacheArrayLength._handle_loops(f.nodes, non_optimal_array_len_usages)

        return non_optimal_array_len_usages

    @staticmethod
    def _get_non_optimal_array_len_usages(functions: List[Function]) -> List[Node]:
        """
        Finds non-optimal usages of array length in loop conditions in given functions.
        """
        non_optimal_array_len_usages: List[Node] = []

        for f in functions:
            non_optimal_array_len_usages += (
                CacheArrayLength._get_non_optimal_array_len_usages_for_function(f)
            )

        return non_optimal_array_len_usages

    def _detect(self):
        results = []

        non_optimal_array_len_usages = CacheArrayLength._get_non_optimal_array_len_usages(
            self.compilation_unit.functions
        )
        for usage in non_optimal_array_len_usages:
            info = [
                "Loop condition ",
                usage,
                " should use cached array length instead of referencing `length` member "
                "of the storage array.\n ",
            ]
            res = self.generate_result(info)
            results.append(res)
        return results
