from decimal import Decimal
from typing import Union, List, Optional, TYPE_CHECKING

from slither.slithir.operations.internal_dynamic_call import InternalDynamicCall
from slither.slithir.operations.solidity_call import SolidityCall

if TYPE_CHECKING:
    from slither.analyses.data_flow.analyses.interval.managers.reference_handler import (
        ReferenceHandler,
    )

from loguru import logger

from slither.analyses.data_flow.analyses.interval.analysis.domain import (
    DomainVariant,
    IntervalDomain,
)
from slither.analyses.data_flow.analyses.interval.core.interval_refiner import IntervalRefiner
from slither.analyses.data_flow.analyses.interval.core.types.range_variable import RangeVariable
from slither.analyses.data_flow.analyses.interval.core.types.value_set import ValueSet
from slither.analyses.data_flow.analyses.interval.core.types.interval_range import IntervalRange
from slither.analyses.data_flow.analyses.interval.managers.arithmetic_solver_manager import (
    ArithmeticSolverManager,
)
from slither.analyses.data_flow.analyses.interval.managers.constraint_store_manager import (
    ConstraintStoreManager,
)
from slither.analyses.data_flow.analyses.interval.managers.operand_analysis_manager import (
    OperandAnalysisManager,
)
from slither.analyses.data_flow.analyses.interval.managers.variable_info_manager import (
    VariableInfoManager,
)
from slither.analyses.data_flow.analyses.interval.managers.reference_handler import (
    ReferenceHandler,
)
from slither.core.solidity_types.elementary_type import ElementaryType
from slither.core.variables.variable import Variable
from slither.slithir.operations.binary import Binary, BinaryType
from slither.slithir.variables.constant import Constant

from IPython import embed


class ConstraintApplierHandler:
    """Handles applying comparison constraints to the domain."""

    def __init__(
        self,
        constraint_store: ConstraintStoreManager,
        reference_handler: Optional[ReferenceHandler] = None,
    ) -> None:
        self.constraint_store = constraint_store
        self.variable_manager = VariableInfoManager()
        self.operand_analyzer = OperandAnalysisManager()
        self.arithmetic_solver = ArithmeticSolverManager()
        self.reference_handler = reference_handler
        # Track applied constraints to prevent duplicates
        self._applied_constraints = set()

    def apply_constraint_from_variable(
        self, condition_variable: Variable, domain: IntervalDomain, operation: SolidityCall
    ) -> None:
        """Apply a constraint from a condition variable (used by require/assert functions)."""

        condition_variable_name = self.variable_manager.get_variable_name(condition_variable)

        # Handle literal values (e.g., assert(false), require(true))
        if isinstance(condition_variable, Constant):
            self._handle_literal_constraint(condition_variable, domain, operation)
            return

        # Check if variable exists in domain state
        if not domain.state.has_range_variable(condition_variable_name):
            logger.error(f"Variable '{condition_variable_name}' not found in domain state")
            raise ValueError(f"Variable '{condition_variable_name}' not found in domain state")

        # Check if it was assigned from a temporary variable (bool r=x>50; require(r))
        temp_var_name = domain.state.get_temp_var_for_local(condition_variable_name)

        # If no mapping exists, condition variable is the temporary variable itself (require(x>50))
        if temp_var_name is None:
            temp_var_name = condition_variable_name

        stored_constraint = self.constraint_store.get_variable_constraint(temp_var_name)

        logger.info(
            f"variable constraint: {temp_var_name}, stored_constraint: {stored_constraint}, operation: {operation}"
        )

        # embed()

        if stored_constraint is None:
            logger.debug(
                f"No constraint found for variable {temp_var_name}, skipping constraint application"
            )
            return

        # Handle different types of stored constraints
        if isinstance(stored_constraint, Binary):
            from slither.analyses.data_flow.analyses.interval.managers.condition_validity_checker_manager import (
                ConditionValidityChecker,
            )
            from slither.analyses.data_flow.analyses.interval.managers.operand_analysis_manager import (
                OperandAnalysisManager,
            )

            # Create condition validity checker to check if constraint can be satisfied
            operand_analyzer = OperandAnalysisManager()
            condition_checker = ConditionValidityChecker(self.variable_manager, operand_analyzer)

            if not condition_checker.is_condition_valid(stored_constraint, domain):
                logger.info(
                    f"Condition {stored_constraint} cannot be satisfied - setting domain to TOP"
                )
                domain.variant = DomainVariant.TOP
                return

            self._apply_comparison_constraint(stored_constraint, domain)
        elif isinstance(stored_constraint, Variable):
            # For Variable constraints, we can't apply comparison constraints directly
            # This typically happens when a variable is used in a condition
            logger.debug(
                f"Variable constraint {stored_constraint} cannot be applied as comparison constraint"
            )
            return
        else:
            # For other operation types (like InternalDynamicCall), we can't apply comparison constraints
            logger.debug(
                f"Operation type {type(stored_constraint)} cannot be applied as comparison constraint"
            )
            return

    def _handle_literal_constraint(
        self, condition_variable: Constant, domain: IntervalDomain, operation: SolidityCall
    ) -> None:
        """Handle literal constraints in require/assert functions."""
        # Check if it's a boolean literal
        if isinstance(condition_variable.value, bool):
            if not condition_variable.value:  # false
                # assert(false) or require(false) - set domain to TOP (unreachable)
                logger.info("Literal false detected in require/assert - setting domain to TOP")
                domain.variant = DomainVariant.TOP
                return
            else:  # true
                # assert(true) or require(true) - no constraint needed, continue
                logger.info("Literal true detected in require/assert - no constraint needed")
                return
        else:
            # Non-boolean literal - create range variable and apply constraint
            logger.info(f"Non-boolean literal detected: {condition_variable.value}")
            condition_variable_name = self.variable_manager.get_variable_name(condition_variable)
            condition_variable_type = self.variable_manager.get_variable_type(condition_variable)

            # Create range variable for the literal
            if self._create_range_variable_for_literal(condition_variable, domain):
                # Now try to apply constraint - but for literals, there's usually no stored constraint
                # So we just log that we created the range variable
                logger.debug(f"Created range variable for literal: {condition_variable_name}")
            else:
                logger.warning(
                    f"Could not create range variable for literal: {condition_variable.value}"
                )

    def _create_range_variable_for_literal(
        self, literal_variable: Constant, domain: IntervalDomain
    ) -> bool:
        """Create a range variable for a literal/constant if possible."""
        import decimal
        from decimal import Decimal

        # Only handle constants/literals
        if not isinstance(literal_variable, Constant):
            return False

        literal_var_name = self.variable_manager.get_variable_name(literal_variable)
        literal_var_type = self.variable_manager.get_variable_type(literal_variable)

        # Only create range variables for numeric types
        if not self.variable_manager.is_type_numeric(literal_var_type):
            return False

        # Convert constant value to Decimal
        constant_val = literal_variable.value
        try:
            if isinstance(constant_val, bool):
                value = Decimal(1) if constant_val else Decimal(0)
            elif isinstance(constant_val, (bytes, bytearray)):
                value = Decimal(int.from_bytes(constant_val, byteorder="big"))
            elif isinstance(constant_val, str):
                s = constant_val
                if s.startswith("0x") or s.startswith("0X"):
                    value = Decimal(int(s, 16))
                else:
                    # If it looks like hex bytecode (only hex chars, even length), parse as hex
                    hs = s.strip()
                    if len(hs) % 2 == 0 and all(c in "0123456789abcdefABCDEF" for c in hs):
                        try:
                            value = Decimal(int(hs, 16))
                        except Exception:
                            value = Decimal(0)
                    else:
                        value = Decimal(str(s))
            else:
                value = Decimal(str(constant_val))

            # Create range variable with the exact value
            range_variable = RangeVariable(
                interval_ranges=None,
                valid_values=ValueSet([value]),
                invalid_values=None,
                var_type=literal_var_type,
            )

            # Store in domain state
            domain.state.set_range_variable(literal_var_name, range_variable)
            return True

        except (ValueError, TypeError, decimal.InvalidOperation):
            # If conversion fails, return False
            return False

    def _apply_comparison_constraint(
        self, comparison_operation: Binary, domain: IntervalDomain
    ) -> None:
        """Apply a comparison constraint to the domain."""
        # Create a unique identifier for this constraint to prevent duplicates
        logger.info(
            f"Applying comparison constraint: {comparison_operation}, type: {type(comparison_operation)}"
        )
        constraint_id = self._create_constraint_id(comparison_operation)

        if constraint_id in self._applied_constraints:
            logger.debug(f"Skipping duplicate constraint: {constraint_id}")
            return

        # Mark this constraint as applied
        self._applied_constraints.add(constraint_id)

        # logger.debug(f"Applying comparison constraint: {comparison_operation.type}")

        # Apply the comparison operation to the domain
        left_operand = comparison_operation.variable_left
        right_operand = comparison_operation.variable_right
        operation_type = comparison_operation.type

        # Check if this is an arithmetic operation comparison (e.g., TMP_0 > 50 where TMP_0 = x + 10)
        if self._is_arithmetic_operation(left_operand) or self._is_arithmetic_operation(
            right_operand
        ):
            self._apply_arithmetic_comparison_constraint(
                left_operand, right_operand, operation_type, domain
            )
        else:
            # Apply simple comparison constraint (e.g., x > 50)
            self._apply_comparison_to_domain(left_operand, right_operand, operation_type, domain)

        # Check if domain should become BOTTOM after constraint application
        self._check_and_convert_to_bottom_if_empty(domain)

    def _apply_comparison_to_domain(
        self,
        left_operand: Union[Variable, Constant],
        right_operand: Union[Variable, Constant],
        operation_type: BinaryType,
        domain: IntervalDomain,
    ) -> None:
        """Apply a comparison constraint to the domain state."""
        try:
            # Determine which operands are variables vs constants
            left_is_variable = self._is_variable(left_operand)
            right_is_variable = self._is_variable(right_operand)

            # Define the four possible comparison scenarios
            variable_compared_to_constant = left_is_variable and not right_is_variable
            constant_compared_to_variable = right_is_variable and not left_is_variable
            variable_compared_to_variable = left_is_variable and right_is_variable
            constant_compared_to_constant = not left_is_variable and not right_is_variable

            if variable_compared_to_constant:
                # Case: variable op constant (e.g., x < 10, x > 5, x == 7)
                self._apply_variable_constant_constraint(
                    left_operand, right_operand, operation_type, domain
                )

            elif constant_compared_to_variable:
                # Case: constant op variable (e.g., 5 < x, 10 > x) - flip the operation
                flipped_operation = IntervalRefiner.flip_comparison_operator(operation_type)
                self._apply_variable_constant_constraint(
                    right_operand, left_operand, flipped_operation, domain
                )

            elif variable_compared_to_variable:
                # Case: variable op variable (e.g., x < y, x > z)
                self._apply_variable_variable_constraint(
                    left_operand, right_operand, operation_type, domain
                )

            # elif constant_compared_to_constant:
            #     # Case: constant op constant - no variables to constrain
            #     # logger.debug(
            #     #     f"Constant comparison: {left_operand} {operation_type} {right_operand}"
            #     # )

        except Exception as e:
            logger.error(f"Error applying comparison to domain: {e}")
            raise

    def _is_variable(self, operand: Union[Variable, Constant]) -> bool:
        """Check if operand is a variable (not a constant)."""
        return not isinstance(operand, Constant)

    def _is_reference_variable(self, variable: Variable) -> bool:
        """Check if variable is a reference variable that needs constraint propagation."""
        if not self.reference_handler:
            return False

        var_name = self.variable_manager.get_variable_name(variable)
        target_var_name = self.reference_handler.get_target_for_reference(var_name)

        # If there's a target mapping, this is a reference variable
        return target_var_name is not None

    def _apply_variable_constant_constraint(
        self,
        variable_operand: Variable,
        constant_operand: Constant,
        operation_type: BinaryType,
        domain: IntervalDomain,
    ) -> None:
        """Apply constraint for variable < constant case."""
        try:
            # Use RangeVariable.get_variable_info to handle reference variables
            logger.info(
                f"Applying variable-constant constraint: {variable_operand} {operation_type} {constant_operand}"
            )
            range_var = RangeVariable.get_variable_info(domain, variable_operand)

            # Extract constant value
            if hasattr(constant_operand, "value"):
                constant_value = constant_operand.value
            else:
                # logger.debug(f"Could not extract constant value from {constant_operand}")
                return

            # Apply the constraint by modifying the range variable's intervals
            IntervalRefiner.refine_variable_range(range_var, constant_value, operation_type)

            # Only propagate constraints for reference variables (struct fields, etc.)
            # Local variables don't need constraint propagation - they are the actual variables
            if self._is_reference_variable(variable_operand):
                self._propagate_constraints_from_reference_to_target(variable_operand, domain)

        except Exception as e:
            logger.error(f"Error applying variable-constant constraint: {e}")
            raise

    def _apply_variable_variable_constraint(
        self,
        left_variable: Variable,
        right_variable: Variable,
        operation_type: BinaryType,
        domain: IntervalDomain,
    ) -> None:
        """Apply constraint for variable < variable case."""
        try:
            left_var_name = self.variable_manager.get_variable_name(left_variable)
            right_var_name = self.variable_manager.get_variable_name(right_variable)

            left_range_var = domain.state.get_range_variable(left_var_name)
            right_range_var = domain.state.get_range_variable(right_var_name)

            if left_range_var is None or right_range_var is None:
                # logger.debug(
                #     f"Missing range variables for variable-variable constraint: {left_var_name} {operation_type} {right_var_name}"
                # )
                return

            # For now, just log - variable-variable constraints are more complex
            # and would require intersection of ranges
            # logger.debug(f"Variable-variable constraint application - implementation needed")

        except Exception as e:
            logger.error(f"Error applying variable-variable constraint: {e}")
            raise

    def _is_arithmetic_operation(self, operand: Union[Variable, Constant]) -> bool:
        """Check if operand is a temporary variable that represents an arithmetic operation."""
        if isinstance(operand, Variable):
            var_name = self.variable_manager.get_variable_name(operand)
            # Check if this is a temporary variable that might contain an arithmetic operation
            if var_name.startswith("TMP_"):
                # Check if there's a stored constraint for this temp variable
                stored_constraint = self.constraint_store.get_variable_constraint(var_name)
                if stored_constraint and isinstance(stored_constraint, Binary):

                    arithmetic_operation_types = {
                        BinaryType.ADDITION,
                        BinaryType.SUBTRACTION,
                        BinaryType.MULTIPLICATION,
                        BinaryType.DIVISION,
                    }
                    return stored_constraint.type in arithmetic_operation_types
        return False

    def _apply_arithmetic_comparison_constraint(
        self,
        left_operand: Union[Variable, Constant],
        right_operand: Union[Variable, Constant],
        operation_type: BinaryType,
        domain: IntervalDomain,
    ) -> None:
        """Apply constraint for arithmetic operation comparisons."""
        try:
            # Determine which operand is the arithmetic operation and which is the constant
            arithmetic_operand = None
            constant_operand = None

            if self._is_arithmetic_operation(left_operand):
                arithmetic_operand = left_operand
                constant_operand = right_operand
            elif self._is_arithmetic_operation(right_operand):
                arithmetic_operand = right_operand
                constant_operand = left_operand
                # Flip the operation for arithmetic solver
                operation_type = IntervalRefiner.flip_comparison_operator(operation_type)

            if arithmetic_operand is None or constant_operand is None:
                # logger.debug("Could not identify arithmetic operand in constraint")
                return

            # Get the stored arithmetic operation
            var_name = self.variable_manager.get_variable_name(arithmetic_operand)
            stored_constraint = self.constraint_store.get_variable_constraint(var_name)

            if not isinstance(stored_constraint, Binary):
                # logger.debug("Stored constraint is not a binary operation")
                return

            # Extract constant value from the comparison
            if isinstance(constant_operand, Constant):
                constraint_value = Decimal(str(constant_operand.value))
            elif isinstance(constant_operand, Variable):
                # Check if this variable is effectively a constant (single value)
                if not self.operand_analyzer.is_operand_constant(constant_operand, domain):
                    # logger.debug("Variable operand is not effectively a constant")
                    return

                constant_var_name = self.variable_manager.get_variable_name(constant_operand)
                if not domain.state.has_range_variable(constant_var_name):
                    # logger.debug("Constant variable not found in domain state")
                    return

                constant_range_var = domain.state.get_range_variable(constant_var_name)
                valid_values = constant_range_var.get_valid_values()
                if not valid_values:
                    # logger.debug("Constant variable has no valid values")
                    return

                constraint_value = list(valid_values)[0]
            else:
                # logger.debug("Constant operand is neither Constant nor Variable type")
                return

            # Use arithmetic solver to solve the constraint
            self.arithmetic_solver.solve_arithmetic_constraint(
                stored_constraint, constraint_value, operation_type, domain
            )

        except Exception as e:
            logger.error(f"Error applying arithmetic comparison constraint: {e}")
            raise

    def create_constant_value_range_variable(
        self,
        target_variable_name: str,
        constant_value: Constant,
        variable_type: ElementaryType,
        domain: IntervalDomain,
    ) -> None:
        """Create a range variable with exact constant value constraint."""
        constant_decimal_value = Decimal(str(constant_value.value))

        # Create a range variable with only the exact constant value (no intervals needed)
        constant_range_variable = RangeVariable(
            interval_ranges=None,
            valid_values=ValueSet({constant_decimal_value}),
            invalid_values=ValueSet(set()),
            var_type=variable_type,
        )

        # Set the constant range variable in domain state
        domain.state.set_range_variable(target_variable_name, constant_range_variable)

    def _propagate_constraints_from_reference_to_target(
        self, variable_operand: Variable, domain: IntervalDomain
    ) -> None:
        # Propagate constraints from reference variables to their targets
        try:
            var_name = self.variable_manager.get_variable_name(variable_operand)

            # Use the reference handler to get target mapping
            if not self.reference_handler:
                logger.error(
                    f"Reference handler not available for constraint propagation from {var_name}"
                )
                raise ValueError(
                    f"Reference handler not available for constraint propagation from {var_name}"
                )

            target_var_name = self.reference_handler.get_target_for_reference(var_name)
            if not target_var_name:
                logger.error(f"No target mapping found for reference variable {var_name}")
                raise ValueError(f"No target mapping found for reference variable {var_name}")

            # Apply constraint propagation from reference to target
            ref_range_var = domain.state.get_range_variable(var_name)
            if not ref_range_var:
                return

            target_range_var = domain.state.get_range_variable(target_var_name)
            if not target_range_var:
                logger.error(
                    f"Target variable '{target_var_name}' not found in domain state for constraint propagation"
                )
                raise ValueError(
                    f"Target variable '{target_var_name}' not found in domain state for constraint propagation"
                )

            # Apply constraint by intersecting the target's range with the reference's constrained range
            target_range_var.apply_constraint_from_reference(ref_range_var)

            # logger.debug(f"Propagated constraints from {var_name} to {target_var_name}")

        except Exception as e:
            logger.error(f"Could not propagate constraints from reference {var_name}: {e}")
            raise

    def _check_and_convert_to_bottom_if_empty(self, domain: IntervalDomain) -> None:
        """Check if domain has any valid intervals and convert to BOTTOM if empty."""
        if domain.variant != DomainVariant.STATE:
            return  # Only check STATE domains

        # Check if any variable has valid intervals or values
        has_valid_content = False
        for var_name, range_var in domain.state.get_range_variables().items():
            if range_var.interval_ranges or range_var.valid_values:
                has_valid_content = True
                break

        # Convert to BOTTOM if no valid content remains
        if not has_valid_content:
            logger.info(f"🚫 Converting domain to BOTTOM - no valid intervals remain")
            domain.variant = DomainVariant.BOTTOM

    def _create_constraint_id(self, comparison_operation: Binary) -> str:
        """Create a unique identifier for a constraint to prevent duplicates."""
        if not isinstance(comparison_operation, Binary):
            logger.error(f"Comparison operation is not a binary operation: {comparison_operation}")
            # embed()
            raise ValueError(
                f"Comparison operation is not a binary operation: {comparison_operation}"
            )
        left_name = self.variable_manager.get_variable_name(comparison_operation.variable_left)
        right_name = self.variable_manager.get_variable_name(comparison_operation.variable_right)
        return f"{left_name}_{comparison_operation.type}_{right_name}"
