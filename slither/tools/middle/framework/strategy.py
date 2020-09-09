from collections import defaultdict
from typing import Union, Callable, Any
from abc import ABC, abstractmethod
import z3 as z3
from itertools import count

# from framework.analyzer import Analyzer
from slither.tools.middle.framework.function import AnalysisFunction
from slither.tools.middle.framework.util import InconsistentStateError
from slither.tools.middle.overlay.ast.call import OverlayCall
from slither.tools.middle.overlay.ast.ite import OverlayITE
from slither.tools.middle.overlay.ast.node import OverlayNode
from slither.tools.middle.overlay.ast.unwrap import OverlayUnwrap
from slither.tools.middle.overlay.util import create_hashable, get_all_call_sites_in_function
from slither.slithir.operations import Operation, Binary, BinaryType, Phi, Assignment, Return, Condition, \
    TypeConversion, Length, InternalCall, HighLevelCall, NewContract, SolidityCall
from slither.slithir.variables import Constant


class Strategy(ABC):

    def __init__(self):
        self.analyzer = None

        # Controls whether resolved values get hidden or not. If they are not
        # hidden then you get annotated values.
        self.hide_resolved = True

        # Controls whether the set value commands get send to the strategy or
        # to the analyzer.
        self.set_value_in_strategy = False

        # Controls whether the get value commands get sent to the strategy or
        # to the analyzer.
        self.get_value_in_strategy = False

        # Usually, the analysis should control the way that the fixpoint runs.
        # The only reason for this to be is if we are using a third party solver.
        self.command_fixpoint = False

    def set_analysis(self, analyzer):
        self.analyzer = analyzer

    def update_node(self, node: Union[OverlayCall, OverlayUnwrap, OverlayITE, OverlayNode], func) -> bool:
        """
        This method is able to be called with any OverlayNode type.
        """

        if isinstance(node, OverlayITE):
            return self.update_node_ite(node, func)
        elif isinstance(node, OverlayCall):
            return False
        elif isinstance(node, OverlayUnwrap):
            return False
        elif isinstance(node, OverlayNode):
            return False
        else:
            print("Unimplemented handling node type: {}".format(type(node)))
            exit(-1)

    def update_ir(self, ir: Operation, func) -> bool:
        """
        This method is able to be called with any valid SlithIR operation. In
        general, this method should, for every possible
        type of IR/Overlay node, give semantics to what it means for that
        operation to yield new information. Return True if new information is
        generated and false otherwise. You can use the Analyzer's data store to
        fetch information for operands if needed. This is a sample
        implementation for a concrete strategy that mirrors real execution.
        """

        if isinstance(ir, Binary):
            return self.update_ir_binary(ir, func)
        elif isinstance(ir, Phi):
            return self.update_ir_phi(ir, func)
        elif isinstance(ir, Assignment):
            return self.update_ir_assignment(ir, func)
        elif isinstance(ir, Return):
            return self.update_ir_return(ir, func)
        elif isinstance(ir, Condition):
            return self.update_ir_condition(ir, func)
        elif isinstance(ir, TypeConversion):
            return self.update_ir_type_conversion(ir, func)
        elif isinstance(ir, Length):
            return self.update_ir_length(ir, func)
        elif isinstance(ir, InternalCall):
            return self.update_ir_internal_call(ir, func)
        elif isinstance(ir, NewContract) or isinstance(ir, HighLevelCall):
            return False
        elif isinstance(ir, SolidityCall):
            return False
        else:
            # TODO: change this later
            print("Unimplemented handling IR type: {}".format(type(ir)))
            return False

    def resolve_ir_vars(self) -> bool:
        """
        This method is used to traverse all the nodes and resolve any of them
        that can be resolved in isolation. This will be run frequently to
        fixpoint. Return True if something changed and return False otherwise.
        """
        ret = False
        for (name, func) in self.analyzer.traverse_nodes():
            variable = func.lookup_var_by_name(name)
            if variable is not None:
                if self.update_ir_variable(variable, func):
                    ret = True
        return ret

    def set_value(self, symbolic, value):
        """
        This function only needs to be overwritten if the strategy is managing
        its own values.
        """
        pass

    def get_var_value(self, variable, func):
        """
        This function only needs to be overwritten if the strategy is managing
        resolving its own values.
        """
        pass

    def run_to_fixpoint(self):
        """
        Run the analyzer to fixpoint, this only needs to be overwritten if the
        strategy is managing its own fixpoint execution.
        """
        pass

    @abstractmethod
    def update_ir_variable(self, variable, func: AnalysisFunction) -> bool:
        """
        Resolve this variable in isolation if you can. Return True if new
        information was introduced and false otherwise.
        """
        pass

    @abstractmethod
    def update_ir_binary(self, ir: Binary, func: AnalysisFunction) -> bool:
        pass

    @abstractmethod
    def update_ir_phi(self, ir: Phi, func: AnalysisFunction) -> bool:
        pass

    @abstractmethod
    def update_ir_assignment(self, ir: Assignment, func: AnalysisFunction) -> bool:
        pass

    @abstractmethod
    def update_ir_type_conversion(self, ir: TypeConversion, func: AnalysisFunction) -> bool:
        pass

    @abstractmethod
    def update_ir_length(self, ir: Length, func: AnalysisFunction) -> bool:
        pass

    @abstractmethod
    def update_ir_return(self, ir: Return, func: AnalysisFunction) -> bool:
        pass

    @abstractmethod
    def update_ir_condition(self, ir: Condition, func: AnalysisFunction) -> bool:
        pass

    @abstractmethod
    def update_node_ite(self, node: OverlayITE, func: AnalysisFunction) -> bool:
        pass

    @abstractmethod
    def update_ir_internal_call(self, ir: InternalCall, func: AnalysisFunction) -> bool:
        pass


class ConcreteStrategy(Strategy):
    """
    In general a strategy needs to tell the Analyzer two things.
        1. How to handle each type of IR/Overlay node.
        2. When to downcall and stuff like that (what if you are stuck).
        3. (Possibly) in what order to process the nodes.

    The Analyzer will maintain an association of unique symbolic variables that
    map to information for that variable. This is necessary so that the Analyzer
    can manage the growth of the graph and the propagation of new information.
    There are methods for reading and writing into this association and they are
    meant to be used by the strategy.
    """

    def __init__(self):
        super().__init__()

        # We want the variables to be annotated, not hidden.
        self.hide_resolved = False

    def update_ir_variable(self, variable, func: AnalysisFunction) -> bool:
        if variable is not None and isinstance(variable, Constant) \
                and not self.analyzer.is_var_resolved(variable, func):
            self.analyzer.set_var_value(variable, func, variable.value)
            return True
        return False

    def update_ir_binary(self, ir: Binary, func: AnalysisFunction) -> bool:
        if ir.type == BinaryType.LESS_EQUAL:
            # We cannot compute either operand in the case of <= so we pass
            # in None.
            return self.update_ir_binary_helper(ir, func,
                                                lambda x, y, z: x <= y,
                                                None,
                                                None)
        elif ir.type == BinaryType.SUBTRACTION:
            return self.update_ir_binary_helper(ir, func,
                                                lambda x, y, z: x - y,
                                                lambda x, y, z: x - z,
                                                lambda x, y, z: z + y)
        elif ir.type == BinaryType.ADDITION:
            return self.update_ir_binary_helper(ir, func,
                                                lambda x, y, z: x + y,
                                                lambda x, y, z: z - x,
                                                lambda x, y, z: z - y)
        elif ir.type == BinaryType.LESS:
            return self.update_ir_binary_helper(ir, func,
                                                lambda x, y, z: x < y,
                                                None,
                                                None)
        elif ir.type == BinaryType.GREATER:
            return self.update_ir_binary_helper(ir, func,
                                                lambda x, y, z: x > y,
                                                None,
                                                None)
        elif ir.type == BinaryType.GREATER_EQUAL:
            return self.update_ir_binary_helper(ir, func,
                                                lambda x, y, z: x >= y,
                                                None,
                                                None)
        elif ir.type == BinaryType.MULTIPLICATION:
            return self.update_ir_binary_helper(ir, func,
                                                lambda x, y, z: x * y,
                                                lambda x, y, z: z // x,
                                                lambda x, y, z: z // y)
        elif ir.type == BinaryType.POWER:
            return self.update_ir_binary_helper(ir, func,
                                                lambda x, y, z: x ** y,
                                                None,
                                                None)
        elif ir.type == BinaryType.EQUAL:
            return self.update_ir_binary_helper(ir, func,
                                                lambda x, y, z: x == y,
                                                lambda x, y, z: x if z is True else None,
                                                lambda x, y, z: y if z is True else None)
        elif ir.type == BinaryType.NOT_EQUAL:
            return self.update_ir_binary_helper(ir, func,
                                                lambda x, y, z: x != y,
                                                None,
                                                None)
        elif ir.type == BinaryType.DIVISION:
            return self.update_ir_binary_helper(ir, func,
                                                lambda x, y, z: x // y,
                                                lambda x, y, z: z * x,
                                                lambda x, y, z: z * y)
        elif ir.type == BinaryType.MODULO:
            return self.update_ir_binary_helper(ir, func,
                                                lambda x, y, z: x % y,
                                                None,
                                                None)
        else:
            print("Unimplmented handling Binary instruction type: {}".format(str(ir.type)))
            exit(-1)

    def update_ir_binary_helper(self, ir: Binary, func: AnalysisFunction,
                                compute_result: Callable[[Any, Any, Any], Any],
                                compute_right: Union[Callable[[Any, Any, Any], Any], None],
                                compute_left: Union[Callable[[Any, Any, Any], Any], None]) -> bool:
        """
        This is a generic helper function to compute the results of binary IR
        operations. It takes in 3 lambdas which define what to do when you have:
            1. All arguments are resolved except result
            2. All arguments are resolved except right
            3. All arguments are resolved except left
        It is important to cover all these cases for a binary IR operation
        because we won't necessarily be getting information that allows us to
        perform a left [op] right = result. Sometimes we will have the result
        and the left value and we want to be able to compute the right value. In
        cases where the right or left operands cannot be inferred from the
        result and the other operand, None should be passed in as the lambda
        """
        left_res = self.analyzer.is_var_resolved(ir.variable_left, func)
        right_res = self.analyzer.is_var_resolved(ir.variable_right, func)
        result_res = self.analyzer.is_var_resolved(ir.lvalue, func)

        left_val = self.analyzer.get_var_value(ir.variable_left, func) if left_res else None
        right_val = self.analyzer.get_var_value(ir.variable_right, func) if right_res else None
        result_val = self.analyzer.get_var_value(ir.lvalue, func) if result_res else None

        if left_res and right_res and result_res:
            # Verify that the result is correct. This is equivalent to treating
            # the result as unresolved. This will allow us to find more
            # InconsistentStateErrors than we did before.
            result = compute_result(left_val, right_val, result_val)
            if result is None:
                return False

            self.analyzer.set_var_value(ir.lvalue, func, result)
            return False
        elif left_res and right_res and not result_res:
            # Do the same thing as the above case except return True because we
            # are returning something new not merely verifying a result.
            result = compute_result(left_val, right_val, result_val)
            if result is None:
                return False

            self.analyzer.set_var_value(ir.lvalue, func, result)
            return True
        elif (left_res and not right_res and result_res) and (compute_right is not None):
            # Compute the right result using the given lambda
            result = compute_right(left_val, right_val, result_val)
            if result is None:
                return False

            self.analyzer.set_var_value(ir.variable_right, func, result)
            return True
        elif (not left_res and right_res and result_res) and (compute_left is not None):
            # Compute the left result using the given lambda
            result = compute_left(left_val, right_val, result_val)
            if result is None:
                return False

            self.analyzer.set_var_value(ir.variable_left, func, result)
            return True
        else:
            return False

    def update_ir_phi(self, ir: Phi, func: AnalysisFunction) -> bool:
        """
        A concrete execution handles the phi node in a special way. Since phi
        nodes can only be one of its many arguments. Once one argument is
        resolved, the final result will be resolved and the other arguments will
        never be resolved.
        """
        return False

    def update_ir_assignment(self, ir: Assignment, func: AnalysisFunction):
        """
        A concrete execution handles the assignment node by setting the values
        equal to each other. In other words, knowing either the lvalue or the
        rvalue we can derive the other. As with all the other update methods, we
        return True if new information was introduced but False if otherwise.
        """
        left_resolved = self.analyzer.is_var_resolved(ir.lvalue, func)
        right_resolved = self.analyzer.is_var_resolved(ir.rvalue, func)

        left_val = self.analyzer.get_var_value(ir.lvalue, func) if left_resolved else None
        right_val = self.analyzer.get_var_value(ir.rvalue, func) if right_resolved else None

        if left_resolved and right_resolved:
            # Verify that they are equal to each other but return False because
            # we did not derive any new information.
            if left_val != right_val:
                raise InconsistentStateError("Assignment error: {} != {}".format(left_val, right_val))
            return False
        elif left_resolved and not right_resolved:
            # Assign the right node to the value of the left.
            self.analyzer.set_var_value(ir.rvalue, func, left_val)
            return True
        elif right_resolved and not left_resolved:
            # Assign the value of the left node to the right.
            self.analyzer.set_var_value(ir.lvalue, func, right_val)
            return True
        else:
            return False

    def update_ir_type_conversion(self, ir: TypeConversion, func: AnalysisFunction):
        # For now, treat type conversions as assignment.
        # TODO: how are we going to model types?
        left_resolved = self.analyzer.is_var_resolved(ir.lvalue, func)
        right_resolved = self.analyzer.is_var_resolved(ir.variable, func)

        left_val = self.analyzer.get_var_value(ir.lvalue, func) if left_resolved else None
        right_val = self.analyzer.get_var_value(ir.variable, func) if right_resolved else None

        if left_resolved and right_resolved:
            # Verify that the sides are equal to each other but return False as
            # no new information is introduced.
            if left_resolved != right_resolved:
                raise InconsistentStateError("TypeConversion error: {} != {}".format(left_val, right_val))
            return False
        elif left_resolved and not right_resolved:
            self.analyzer.set_var_value(ir.variable, func, left_val)
            return True
        elif right_resolved and not left_resolved:
            self.analyzer.set_var_value(ir.lvalue, func, right_val)
            return True
        else:
            return False

    def update_ir_condition(self, ir: Condition, func: AnalysisFunction) -> bool:
        # We cannot gain any new information from conditions.
        return False

    def update_ir_length(self, ir: Length, func: AnalysisFunction) -> bool:
        # TODO: can we gain information from length statements?
        return False

    def update_ir_return(self, ir: Return, func: AnalysisFunction) -> bool:
        # We cannot gain any new information from returns.
        return False

    def update_node_ite(self, node: OverlayITE, func: AnalysisFunction) -> bool:
        # First, prefetch everything.
        cond_resolved = self.analyzer.is_var_resolved(node.condition, func)
        cond_val = self.analyzer.get_var_value(node.condition, func) if cond_resolved else None

        true_resolved = self.analyzer.is_var_resolved(node.consequence, func)
        true_val = self.analyzer.get_var_value(node.consequence, func) if true_resolved else None

        false_resolved = self.analyzer.is_var_resolved(node.alternative, func)
        false_val = self.analyzer.get_var_value(node.alternative, func) if false_resolved else None

        result_resolved = self.analyzer.is_var_resolved(node.lvalue, func)
        result_val = self.analyzer.get_var_value(node.lvalue, func) if result_resolved else None

        # If the condition is true and we have the true branch value we can evaluate result.
        if cond_resolved and cond_val and true_resolved:
            if result_resolved:
                self.analyzer.set_var_value(node.lvalue, func, true_val)
                return False
            else:
                self.analyzer.set_var_value(node.lvalue, func, true_val)
                return True

        # If the condition is false and we have the false branch value we can evaluate result.
        elif cond_resolved and not cond_val and false_resolved:
            if result_resolved:
                self.analyzer.set_var_value(node.lvalue, func, false_val)
                return False
            else:
                self.analyzer.set_var_value(node.lvalue, func, false_val)
                return True

        # If both branches and result are resolved we can infer cond if the branches are not equal.
        elif result_resolved and true_resolved and false_resolved and not cond_resolved:
            if result_val == true_val and result_val != false_val:
                self.analyzer.set_var_value(node.condition, True)
                return True
            elif result_val == false_val and result_val != true_val:
                self.analyzer.set_var_value(node.condition, False)
                return True

        return False

    def update_ir_internal_call(self, ir: InternalCall, func: AnalysisFunction) -> bool:
        return False


class Range:
    def __init__(self, lower, upper):
        self.lower = lower
        self.upper = upper

    def __str__(self):
        return "[{}, {}]".format(self.lower, self.upper)

    def change_range_to(self, lower, upper):
        self.lower = lower
        self.upper = upper

    def __eq__(self, other):
        if not isinstance(other, Range):
            return False
        if self.lower == other.lower and self.upper == other.upper:
            return True
        return False

    def __add__(self, other):
        return Range(self.lower + other.lower, self.upper + other.upper)

    def __sub__(self, other):
        return Range(self.lower - other.upper, self.upper - other.lower)

    def contains(self, other):
        return self.lower <= other.lower and self.upper >= other.upper


def add_ranges(r1: Range, r2: Range) -> Range:
    return Range(r1.lower + r2.lower, r1.upper + r2.upper)


def subtract_ranges(r1: Range, r2: Range) -> Range:
    return Range(r1.lower - r2.upper, r1.lower - r2.upper)


def is_uninitialized(r) -> bool:
    if not isinstance(r, Range):
        return False
    return r.lower == float('-inf') and r.upper == float('inf')


class SymbolicVariable:
    counter = count()

    def __init__(self, parent):
        self.id = next(self.counter)
        self.parent = parent

    def __str__(self):
        return self.parent.get_sym_value(self)


class SymbolicStrategy(Strategy):
    """
    This sample strategy demonstrates how to use the value store that is
    built into the analyzer to hold symbolic variables whose values are
    contained within the strategy itself. In this case, the only reason we use
    the analyzer for our data_types is for display purposes. Really, all the
    analyzer needs to know is if something has changed for its naive fixpoint
    engine to work. In this case, the analysis will always report that the
    variable of inquiry is resolved, but it is up to the strategy to manage
    the true values of its symbolic variables.

    The kind of tricky part for this analysis is that the native booleans are
    still needed for control flow. It is also going to be somewhat hard to allow
    a strategy to define an interface for accepting user generated values.
    """
    def __init__(self):
        super().__init__()

        # We want the variables to be annotated, not hidden.
        self.hide_resolved = False

        # Since we are using the analyzer to store permanent variables we want
        # to bypass the set_value commands to the analyzer and make them come
        # directly to us.
        self.set_value_in_strategy = True

        self.values = dict()
        self.symvars = set()

    def is_sym_resolved(self, symbolic):
        if symbolic in self.values:
            return not is_uninitialized(self.values[symbolic])
        return False

    def get_sym_value(self, symbolic):
        if symbolic in self.values:
            return str(self.values.get(symbolic))
        else:
            return ""

    def set_value(self, symbolic, value):
        self.values[symbolic] = value

    def update_ir_variable(self, variable, func: AnalysisFunction) -> bool:
        # If the variable has not been resolved yet that means we have not
        # touched it yet. This means we should register a symbolic variable.
        if not self.analyzer.is_var_resolved(variable, func):
            svar = SymbolicVariable(self)
            self.symvars.add(svar)
            self.analyzer.set_var_value(variable, func, svar)

            if isinstance(variable, Constant):
                self.values[svar] = Range(variable.value, variable.value)
            elif 'int' in str(variable.type):
                self.values[svar] = Range(float('-inf'), float('+inf'))
            return True

        return False

    def update_ir_binary(self, ir: Binary, func: AnalysisFunction) -> bool:
        sym_left = self.analyzer.get_var_value(ir.variable_left, func)
        sym_right = self.analyzer.get_var_value(ir.variable_right, func)
        sym_lvalue = self.analyzer.get_var_value(ir.variable_right, func)

        if not isinstance(sym_left, SymbolicVariable) or not isinstance(sym_right, SymbolicVariable):
            return False

        range_left = self.values[sym_left]
        range_right = self.values[sym_right]

        if ir.type == BinaryType.LESS_EQUAL:
            return False
        elif ir.type == BinaryType.SUBTRACTION:
            return False
        elif ir.type == BinaryType.ADDITION:
            return self.update_ir_binary_helper(ir, func,
                                                lambda x, y, z: x + y,
                                                lambda x, y, z: z - x,
                                                lambda x, y, z: z - y)
        elif ir.type == BinaryType.LESS:
            return False
        elif ir.type == BinaryType.GREATER:
            return False
        elif ir.type == BinaryType.MULTIPLICATION:
            return False
        elif ir.type == BinaryType.POWER:
            return False
        elif ir.type == BinaryType.EQUAL:
            return self.update_ir_binary_helper(ir, func,
                                                lambda x, y, z: x == y,
                                                lambda x, y, z: x if z is True else None,
                                                lambda x, y, z: y if z is True else None)
        else:
            print("Unimplmented handling Binary instruction type: {}".format(str(ir.type)))
            exit(-1)

    def update_ir_binary_helper(self, ir: Binary, func: AnalysisFunction,
                                compute_result: Callable[[Any, Any, Any], Any],
                                compute_right: Union[Callable[[Any, Any, Any], Any], None],
                                compute_left: Union[Callable[[Any, Any, Any], Any], None]) -> bool:
        """
        This is a generic helper function to compute the results of binary IR
        operations. It takes in 3 lambdas which define what to do when you have:
            1. All arguments are resolved except result
            2. All arguments are resolved except right
            3. All arguments are resolved except left
        It is important to cover all these cases for a binary IR operation
        because we won't necessarily be getting information that allows us to
        perform a left [op] right = result. Sometimes we will have the result
        and the left value and we want to be able to compute the right value. In
        cases where the right or left operands cannot be inferred from the
        result and the other operand, None should be passed in as the lambda
        """
        left_sym = self.analyzer.get_var_value(ir.variable_left, func)
        right_sym = self.analyzer.get_var_value(ir.variable_right, func)
        result_sym = self.analyzer.get_var_value(ir.lvalue, func)

        # Convert the resolved and value variables into the language of the
        # local executor since this strategy simply uses the analyzer to hold
        # symbolic variables and does all of the processing itself.
        if isinstance(left_sym, SymbolicVariable) and self.is_sym_resolved(left_sym):
            left_val = self.values[left_sym]
        else:
            left_val = None
        if isinstance(right_sym, SymbolicVariable) and self.is_sym_resolved(right_sym):
            right_val = self.values[right_sym]
        else:
            right_val = None
        if isinstance(result_sym, SymbolicVariable) and self.is_sym_resolved(result_sym):
            result_val = self.values[result_sym]
        else:
            result_val = None

        left_res = True if self.is_sym_resolved(left_sym) else False
        right_res = True if self.is_sym_resolved(right_sym) else False
        result_res = True if self.is_sym_resolved(result_sym) else False

        if left_res and right_res and result_res:
            # Verify that the result is correct. This is equivalent to treating
            # the result as unresolved. This will allow us to find more
            # InconsistentStateErrors than we did before.
            result = compute_result(left_val, right_val, result_val)
            if result is None:
                return False

            self.values[result_sym] = result
            return False
        elif left_res and right_res and not result_res:
            # Do the same thing as the above case except return True because we
            # are returning something new not merely verifying a result.
            result = compute_result(left_val, right_val, result_val)
            if result is None:
                return False

            self.values[result_sym] = result
            return True
        elif (left_res and not right_res and result_res) and (compute_right is not None):
            # Compute the right result using the given lambda
            result = compute_right(left_val, right_val, result_val)
            if result is None:
                return False

            self.values[right_sym] = result
            return True
        elif (not left_res and right_res and result_res) and (compute_left is not None):
            # Compute the left result using the given lambda
            result = compute_left(left_val, right_val, result_val)
            if result is None:
                return False

            self.values[left_sym] = result
            return True
        else:
            return False

    def update_ir_phi(self, ir: Phi, func: AnalysisFunction) -> bool:
        return False

    def update_ir_assignment(self, ir: Assignment, func: AnalysisFunction) -> bool:
        sym_left = self.analyzer.get_var_value(ir.lvalue, func)
        sym_right = self.analyzer.get_var_value(ir.rvalue, func)

        if not isinstance(sym_left, SymbolicVariable) or not isinstance(sym_right, SymbolicVariable):
            return False

        assert isinstance(sym_left, SymbolicVariable)
        assert isinstance(sym_right, SymbolicVariable)

        left_res = self.is_sym_resolved(sym_left)
        right_res = self.is_sym_resolved(sym_right)
        range_left = self.values[sym_left]
        range_right = self.values[sym_right]

        if left_res and right_res:
            if range_left == range_right:
                return False
            elif range_left.contains(range_right):
                self.values[sym_left] = self.values[sym_right]
                return True
            elif range_right.contains(range_left):
                self.values[sym_right] = self.values[sym_left]
                return True
            else:
                raise InconsistentStateError("Cannot reconcile intervals: {} {}".format(range_left, range_right))
        elif left_res and not right_res:
            self.values[sym_right] = self.values[sym_left]
            return True
        elif not left_res and right_res:
            self.values[sym_left] = self.values[sym_right]
            return True
        else:
            # not left_res and not right_res
            return False

    def update_ir_type_conversion(self, ir: TypeConversion, func: AnalysisFunction) -> bool:
        return False

    def update_ir_length(self, ir: Length, func: AnalysisFunction) -> bool:
        return False

    def update_ir_return(self, ir: Return, func: AnalysisFunction) -> bool:
        return False

    def update_ir_condition(self, ir: Condition, func: AnalysisFunction) -> bool:
        return False

    def update_node_ite(self, node: OverlayITE, func: AnalysisFunction) -> bool:
        sym_true = self.analyzer.get_var_value(node.consequence, func)
        sym_false = self.analyzer.get_var_value(node.alternative, func)
        sym_lvalue = self.analyzer.get_var_value(node.lvalue, func)
        sym_cond = self.analyzer.get_var_value(node.condition, func)
        true_resolved = self.is_sym_resolved(sym_true)
        false_resolved = self.is_sym_resolved(sym_false)
        lvalue_resolved = self.is_sym_resolved(sym_lvalue)
        cond_resolved = self.is_sym_resolved(sym_cond)

        # If the condition is not resolved then we cannot deduce anything.
        if not cond_resolved:
            return False
        condition = bool(self.get_sym_value(sym_cond))

        if not lvalue_resolved and true_resolved and condition is True:
            self.values[sym_lvalue] = self.values[sym_true]
            return True
        elif not lvalue_resolved and false_resolved and condition is False:
            self.values[sym_lvalue] = self.values[sym_false]
            return True
        elif lvalue_resolved and not true_resolved and condition is True:
            self.values[sym_true] = self.values[sym_lvalue]
            return True
        elif lvalue_resolved and not false_resolved and condition is False:
            self.values[sym_false] = self.values[sym_lvalue]
            return True
        else:
            return False

    def update_ir_internal_call(self, ir: InternalCall, func: AnalysisFunction) -> bool:
        return False


class ConstraintStrategy(Strategy):
    """
    This sample strategy shows how to use z3 to drive constraint based
    analysis. The nature of z3 requires that we use the "strategy manages
    values" trick from the Symbolic strategy.
    """
    def __init__(self):
        super().__init__()

        # We want the variables to be annotated, not hidden.
        self.hide_resolved = False

        # Since we are using the analyzer to store permanent variables we want
        # to bypass the set_value commands to the analyzer and make them come
        # directly to us.
        self.set_value_in_strategy = True
        self.get_value_in_strategy = True

        # We should control the way the fixpoint solver runs.
        self.command_fixpoint = True

        self.values = dict()
        self.symvars = set()

        self.var_values = dict()
        self.user_supplied_constraints = []

        self.opt = z3.Optimize()

    def set_value(self, symbolic, value):
        assert False

    def get_var_value(self, variable, func):
        return str(self.var_values[self.values[create_hashable(variable, func)]])

    def initialize_ir_variable(self, variable, func: AnalysisFunction) -> bool:
        # Create a symbolic variable
        if isinstance(variable, Constant):
            if 'int' in str(variable.type):
                self.values[create_hashable(variable, func)] = x = z3.Int(str(variable))
                self.opt.add(x == variable.value)
        elif 'int' in str(variable.type):
            self.values[create_hashable(variable, func)] = x = z3.Int(str(variable))
        elif 'bool' in str(variable.type):
            self.values[create_hashable(variable, func)] = x = z3.Bool(str(variable))
        return True

    def add_interprocedural_constraints(self):
        """Add the interprocedural constraints of the current analyzer."""

        # Link up the arguments and return values of the called functions.
        for func in self.analyzer.live_functions:
            for callsite in get_all_call_sites_in_function(func.under):
                # Make sure that this call is actually resolved.
                if callsite not in func.callees:
                    continue

                caller_function = func
                new_function = func.callees[callsite]

                if isinstance(callsite, OverlayCall):
                    # Link up the arguments.
                    for var in callsite.arguments:
                        if str(var) in callsite.arg_as_map:
                            for as_var in callsite.arg_as_map[str(var)]:
                                z_asvar = self.values[create_hashable(as_var, caller_function)]
                                z_var = self.values[create_hashable(var, new_function)]
                                self.opt.add(z_asvar == z_var)
                        else:
                            z_var_caller = self.values[create_hashable(var, caller_function)]
                            z_var_callee = self.values[create_hashable(var, new_function)]
                            self.opt.add(z_var_caller == z_var_callee)

                    # Link up return values.
                    for var in callsite.returns:
                        if str(var) in callsite.ret_as_map:
                            for as_var in callsite.ret_as_map[str(var)]:
                                z_var = self.values[create_hashable(var, caller_function)]
                                z_asvar = self.values[create_hashable(as_var, new_function)]
                                self.opt.add(z_var == z_asvar)
                        else:
                            z_var_caller = self.values[create_hashable(var, caller_function)]
                            z_var_callee = self.values[create_hashable(var, new_function)]
                            self.opt.add(z_var_caller == z_var_callee)

                elif isinstance(callsite, InternalCall) or isinstance(callsite, HighLevelCall):
                    # In the InternalCall case, things are a bit more complicated
                    # because we want to link the argument and return variables which
                    # are often represented by physically different variables in the IR.
                    assert (len(callsite.arguments) == len(callsite.function.parameters_ssa))
                    for i in range(len(callsite.arguments)):
                        if isinstance(callsite.arguments[i], Constant):
                            # We may have to add constants to a new_function
                            if callsite.arguments[i] not in new_function.var_to_symvar_local:
                                symvar = new_function.analyzer.symbolize_var(callsite.arguments[i], new_function)
                                new_function.set_sym_var_local(callsite.arguments[i], symvar)

                        z_var_caller = self.values[create_hashable(callsite.arguments[i], caller_function)]
                        # A nasty hack to accomadate slither's weird SSA form.
                        z_var_callee = self.values[create_hashable(str(new_function.under.func.parameters[i]) + "_1", new_function)]
                        self.opt.add(z_var_caller == z_var_callee)

                    if len(callsite.function.return_values_ssa) == 1:
                        z_lvalue = self.values[create_hashable(callsite.lvalue, caller_function)]
                        z_retval = self.values[create_hashable(callsite.function.return_values_ssa[0], new_function)]
                        self.opt.add(z_lvalue == z_retval)

        # If a function has been downcalled, make sure to propagate that information
        # to force that path to be true.
        for func in self.analyzer.live_functions:
            for callsite in get_all_call_sites_in_function(func.under):
                # Only consider InternalCalls because OverlayCalls can be explored
                # without commitment.
                if isinstance(callsite, InternalCall):
                    if callsite in func.callees:
                        self.assert_path_from_root(func)

    def assert_path_from_root(self, func):
        current = func
        while current != self.analyzer.root:
            assert len(current.callers) == 1
            parent = current.callers[0]

            # Find the callsite in the parent and if its conditional then mark
            # it as true.
            callsite = next((k for (k, v) in parent.callees.items() if v == current), None)
            if callsite is None:
                print("ERROR: could not find callsite for funtion")
                exit(-1)
            if isinstance(callsite, OverlayCall):
                z_condvar = self.values[create_hashable(callsite.cond, parent)]
                if not callsite.cond_complement:
                    self.opt.add(z_condvar == True)
                else:
                    self.opt.add(z_condvar == False)
            current = parent

    def run_to_fixpoint(self):
        self.opt = z3.Optimize()

        self.var_values.clear()

        # Add variables if they aren't added already
        for (name, func) in self.analyzer.traverse_nodes():
            variable = func.lookup_var_by_name(name)
            if variable is not None:
                self.initialize_ir_variable(variable, func)

        # Add constraints based on the IR instructions
        for func in self.analyzer.live_functions:
            for stmt in func.under.statements:
                self.update_node(stmt, func)
                for ir in stmt.ir:
                    self.update_ir(ir, func)

        # Add the user supplied constraints
        for constraint in self.user_supplied_constraints:
            self.opt.add(constraint)

        # Add interprocedural constraints
        self.add_interprocedural_constraints()

        # Provide one possible solution
        status = self.opt.check()
        if status == z3.unsat:
            # Try to jettison the last user supplied constraint
            if len(self.user_supplied_constraints) >= 1:
                self.user_supplied_constraints.pop()
            raise InconsistentStateError("unsatisfiable constraints")
        m = self.opt.model()

        for var, z_var in self.values.items():
            if m[z_var] is None:
                # The value is unconstrained so we have no idea what it could be
                self.var_values[z_var] = '?'
            elif z3.is_int(z_var):
                self.var_values[z_var] = m[z_var].as_long()
            elif z3.is_bool(z_var):
                self.var_values[z_var] = self.boolref_to_bool(m[z_var])

    def boolref_to_bool(self, z_var):
        assert z3.is_bool(z_var)
        if z3.is_true(z_var):
            return True
        else:
            return False

    def update_node(self, node: Union[OverlayCall, OverlayUnwrap, OverlayITE, OverlayNode], func) -> bool:
        if isinstance(node, OverlayITE):
            return self.update_node_ite(node, func)
        elif isinstance(node, OverlayCall):
            return False
        elif isinstance(node, OverlayUnwrap):
            return False
        elif isinstance(node, OverlayNode):
            return False
        else:
            print("Unimplemented handling node type: {}".format(type(node)))
            exit(-1)

    def update_node_ite(self, node: OverlayITE, func: AnalysisFunction) -> bool:
        z_true = self.values[create_hashable(node.consequence, func)]
        z_false = self.values[create_hashable(node.alternative, func)]
        z_lvalue = self.values[create_hashable(node.lvalue, func)]
        z_cond = self.values[create_hashable(node.condition, func)]

        z_if = z3.If(z_cond, z_true, z_false)
        self.opt.add(z_lvalue == z_if)

        return False

    def update_ir_binary(self, ir: Binary, func: AnalysisFunction) -> bool:
        z_left = self.values[create_hashable(ir.variable_left, func)]
        z_right = self.values[create_hashable(ir.variable_right, func)]
        z_lvalue = self.values[create_hashable(ir.lvalue, func)]

        if ir.type == BinaryType.LESS_EQUAL:
            self.opt.add(z_lvalue == (z_left <= z_right))
        elif ir.type == BinaryType.GREATER_EQUAL:
            self.opt.add(z_lvalue == (z_left >= z_right))
        elif ir.type == BinaryType.SUBTRACTION:
            self.opt.add(z_lvalue == (z_left - z_right))
        elif ir.type == BinaryType.ADDITION:
            self.opt.add(z_lvalue == (z_left + z_right))
        elif ir.type == BinaryType.LESS:
            self.opt.add(z_lvalue == (z_left < z_right))
        elif ir.type == BinaryType.GREATER:
            self.opt.add(z_lvalue == (z_left > z_right))
        elif ir.type == BinaryType.MULTIPLICATION:
            self.opt.add(z_lvalue == (z_left * z_right))
        elif ir.type == BinaryType.POWER:
            return False
        elif ir.type == BinaryType.EQUAL:
            self.opt.add(z_lvalue == (z_left == z_right))
        elif ir.type == BinaryType.NOT_EQUAL:
            self.opt.add(z_lvalue == (z_left != z_right))
        elif ir.type == BinaryType.DIVISION:
            self.opt.add(z_lvalue == (z_left / z_right))
        elif ir.type == BinaryType.MODULO:
            self.opt.add(z_lvalue == (z_left % z_right))
        elif ir.type == BinaryType.OROR:
            self.opt.add(z_lvalue == z3.Or(z_left, z_right))
        elif ir.type == BinaryType.ANDAND:
            self.opt.add(z_lvalue == z3.And(z_left, z_right))
        else:
            print("Unimplmented handling Binary instruction type: {}".format(str(ir.type)))
            exit(-1)

    def update_ir_variable(self, variable, func: AnalysisFunction) -> bool:
        return False

    def update_ir_phi(self, ir: Phi, func: AnalysisFunction) -> bool:
        return False

    def update_ir_assignment(self, ir: Assignment, func: AnalysisFunction) -> bool:
        z_left = self.values[create_hashable(ir.lvalue, func)]
        z_right = self.values[create_hashable(ir.rvalue, func)]
        self.opt.add(z_left == z_right)

    def update_ir_type_conversion(self, ir: TypeConversion, func: AnalysisFunction) -> bool:
        return False

    def update_ir_length(self, ir: Length, func: AnalysisFunction) -> bool:
        return False

    def update_ir_return(self, ir: Return, func: AnalysisFunction) -> bool:
        return False

    def update_ir_condition(self, ir: Condition, func: AnalysisFunction) -> bool:
        return False

    def update_ir_internal_call(self, ir: InternalCall, func: AnalysisFunction) -> bool:
        return False

    def add_constraint(self, s):
        l = s.split()
        for i, e in enumerate(l):
            for func in self.analyzer.live_functions:
                v = func.lookup_var_by_name(e)
                if v is not None:
                    l[i] = "self.values[('{}', {})]".format(str(v), func.id)
        constraint = eval(' '.join(l))
        self.user_supplied_constraints.append(constraint)
        self.opt.add(constraint)

    def find_variable(self, s):
        for function in self.analyzer.live_functions:
            v = function.lookup_var_by_name(s)
            if v is not None:
                return v, function
            return None, None
