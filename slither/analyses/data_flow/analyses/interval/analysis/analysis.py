from typing import List, Optional, Tuple, Union
from decimal import Decimal

from loguru import logger

from slither.core.declarations.contract import Contract
from slither.core.solidity_types.type_alias import TypeAlias, TypeAliasTopLevel

from slither.analyses.data_flow.analyses.interval.analysis.domain import (
    DomainVariant,
    IntervalDomain,
)
from slither.analyses.data_flow.analyses.interval.core.types.interval_range import IntervalRange
from slither.analyses.data_flow.analyses.interval.core.types.range_variable import RangeVariable
from slither.analyses.data_flow.analyses.interval.core.types.value_set import ValueSet
from slither.analyses.data_flow.analyses.interval.handlers.operation_handler import OperationHandler
from slither.analyses.data_flow.analyses.interval.managers.condition_validity_checker_manager import (
    ConditionValidityChecker,
)
from slither.analyses.data_flow.analyses.interval.managers.constraint_manager import (
    ConstraintManager,
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
from slither.analyses.data_flow.analyses.interval.analysis.widening import Widening
from slither.analyses.data_flow.engine.analysis import Analysis
from slither.analyses.data_flow.engine.direction import Direction, Forward
from slither.analyses.data_flow.engine.domain import Domain
from slither.core.cfg.node import Node
from slither.core.declarations.contract import Contract
from slither.core.declarations.function_contract import FunctionContract
from slither.core.declarations.function_top_level import FunctionTopLevel
from slither.core.solidity_types.elementary_type import ElementaryType
from slither.core.solidity_types.user_defined_type import UserDefinedType
from slither.core.solidity_types.array_type import ArrayType
from slither.core.variables.variable import Variable
from slither.slithir.operations.assignment import Assignment
from slither.slithir.operations.binary import Binary, BinaryType
from slither.slithir.operations.high_level_call import HighLevelCall
from slither.slithir.operations.internal_call import InternalCall
from slither.slithir.operations.library_call import LibraryCall
from slither.slithir.operations.operation import Operation
from slither.slithir.operations.solidity_call import SolidityCall
from slither.slithir.variables.temporary import TemporaryVariable
from slither.slithir.operations.member import Member
from slither.slithir.operations.length import Length
from slither.slithir.operations.type_conversion import TypeConversion
from slither.slithir.operations.index import Index
from slither.slithir.operations.unary import Unary, UnaryType


class IntervalAnalysis(Analysis):
    """Interval analysis for data flow analysis."""

    ARITHMETIC_OPERATORS: set[BinaryType] = {
        BinaryType.ADDITION,
        BinaryType.SUBTRACTION,
        BinaryType.MULTIPLICATION,
        BinaryType.DIVISION,
        BinaryType.MODULO,
        BinaryType.POWER,
        BinaryType.LEFT_SHIFT,
        BinaryType.RIGHT_SHIFT,
        BinaryType.AND,
        BinaryType.OR,
        BinaryType.CARET,
    }

    # Comparison operators
    COMPARISON_OPERATORS: set[BinaryType] = {
        BinaryType.GREATER,
        BinaryType.LESS,
        BinaryType.GREATER_EQUAL,
        BinaryType.LESS_EQUAL,
        BinaryType.EQUAL,
        BinaryType.NOT_EQUAL,
    }

    BOOLEAN_OPERATORS: set[BinaryType] = {
        BinaryType.ANDAND,
        BinaryType.OROR,
    }

    def __init__(self) -> None:
        self._direction: Direction = Forward()
        self._reference_handler = ReferenceHandler()
        # Use the reference handler for constraint manager
        self._constraint_manager = ConstraintManager(self._reference_handler)
        # Pass the same constraint manager instance to OperationHandler
        self._operation_handler = OperationHandler(
            self._reference_handler, self._constraint_manager
        )
        self._variable_info_manager = VariableInfoManager()
        self._operand_analyzer = OperandAnalysisManager()
        self._condition_validity_checker = ConditionValidityChecker(
            self._variable_info_manager, self._operand_analyzer
        )
        self._widening = Widening()

    def domain(self) -> Domain:
        return IntervalDomain.with_state({})

    def direction(self) -> Direction:
        return self._direction

    def bottom_value(self) -> Domain:
        return IntervalDomain.bottom()

    def is_condition_valid(self, condition: Operation, domain: IntervalDomain) -> bool:
        """Check if a condition can be satisfied given the current domain state."""
        return self._condition_validity_checker.is_condition_valid(condition, domain)

    def apply_condition(
        self,
        domain: IntervalDomain,
        condition: Operation,
        branch_taken: bool,
        condition_variable: Variable,
    ) -> IntervalDomain:
        """Apply branch filtering based on the condition and which branch is taken.

        Example: For condition "x > 100" in "if (x > 100) { ... } else { ... }":
        - branch_taken=True: applies constraint x > 100 (then branch)
        - branch_taken=False: applies constraint x <= 100 (else branch)
        """

        if not isinstance(condition, Binary):
            return domain

        # Create a copy of the domain to avoid modifying the original
        filtered_domain = domain.deep_copy()

        list_of_conditions = self.condition_extractor(condition_variable)

        if branch_taken:
            return self._apply_then_branch_condition(filtered_domain, list_of_conditions)
        else:
            return self._apply_else_branch_condition(filtered_domain, list_of_conditions)

    def condition_extractor(
        self, condition_variable: Union[Variable, Binary, Unary]
    ) -> List[Tuple[Union[Binary, Unary], bool]]:
        """Recursively extracts all operations with negation flags."""
        return self._condition_extractor_helper(condition_variable, is_negated=False)

    def _condition_extractor_helper(
        self, condition_variable: Union[Variable, Binary, Unary], is_negated: bool
    ) -> List[Tuple[Union[Binary, Unary], bool]]:
        """Helper that tracks negation state through recursion."""

        constraint = self._constraint_manager.get_variable_constraint(condition_variable.name)
        logger.info(f"Constraint: {constraint}, type: {type(constraint)}, negated: {is_negated}")

        # If no constraint found, return empty list (base case for actual variables like 'a')
        if constraint is None:
            return []

        # Recursively follow Variable constraints
        if isinstance(constraint, Variable):
            return self._condition_extractor_helper(constraint, is_negated)

        # If it's a Unary BANG operation - flip the negation flag
        if isinstance(constraint, Unary):
            if constraint.type == UnaryType.BANG:
                # BANG flips the negation state
                # The rvalue should be a Variable containing the actual condition
                if isinstance(constraint.rvalue, Variable):
                    return self._condition_extractor_helper(constraint.rvalue, not is_negated)
                else:
                    logger.error(f"Unary BANG operand is not a Variable: {constraint.rvalue}")
                    return []
            else:
                logger.error(f"Unsupported unary operation: {constraint.type}")
                return []

        # If it's a Binary operation
        if isinstance(constraint, Binary):
            # Only include comparison and boolean operations, not arithmetic operations
            if (
                constraint.type in self.COMPARISON_OPERATORS
                or constraint.type in self.BOOLEAN_OPERATORS
            ):
                operations = [
                    (constraint, is_negated)
                ]  # Include this operation with its negation state
            else:
                operations = []  # Skip arithmetic operations - they're not conditions

            # Recursively expand left operand if it's a variable AND has a stored constraint
            if isinstance(constraint.variable_left, Variable):
                left_constraint = self._constraint_manager.get_variable_constraint(
                    constraint.variable_left.name
                )
                if left_constraint is not None:
                    operations.extend(
                        self._condition_extractor_helper(constraint.variable_left, is_negated)
                    )

            # Recursively expand right operand if it's a variable AND has a stored constraint
            if isinstance(constraint.variable_right, Variable):
                right_constraint = self._constraint_manager.get_variable_constraint(
                    constraint.variable_right.name
                )
                if right_constraint is not None:
                    operations.extend(
                        self._condition_extractor_helper(constraint.variable_right, is_negated)
                    )

            return operations

        return []

    def _apply_then_branch_condition(
        self, domain: IntervalDomain, conditions: List[Tuple[Union[Binary, Unary], bool]]
    ) -> IntervalDomain:
        """Apply conditions when the then branch is taken."""
        if hasattr(self._constraint_manager.constraint_applier, "_applied_constraints"):
            self._constraint_manager.constraint_applier._applied_constraints.clear()

        for operation, is_negated in conditions:
            if isinstance(operation, Unary):
                continue

            if operation.type in self.BOOLEAN_OPERATORS:
                continue

            # Skip arithmetic operations - they are not conditions to be negated
            if operation.type in self.ARITHMETIC_OPERATORS:
                continue

            if isinstance(operation, Binary) and operation.type in self.COMPARISON_OPERATORS:
                # Determine the actual operator to apply
                operator_to_apply = operation.type
                if is_negated:
                    operator_to_apply = self._get_negated_operator(operation.type)

                # Only create new comparison if we need to negate
                if is_negated:
                    negated_result_variable = TemporaryVariable(operation.node)
                    negated_result_variable.set_type(operation.lvalue.type)

                    actual_comparison = Binary(
                        result=negated_result_variable,
                        left_variable=operation.variable_left,
                        right_variable=operation.variable_right,
                        operation_type=operator_to_apply,
                    )
                    actual_comparison.set_node(operation.node)
                else:
                    actual_comparison = operation

                # Verify condition validity first
                if not self._condition_validity_checker.is_condition_valid(
                    actual_comparison, domain
                ):
                    return IntervalDomain.top()

                # Apply constraint to the actual variables in the comparison
                if operation.variable_left is not None:
                    left_operand_name = self._variable_info_manager.get_variable_name(
                        operation.variable_left
                    )
                    self._constraint_manager.store_variable_constraint(
                        left_operand_name, actual_comparison
                    )
                    self._constraint_manager.apply_constraint_from_variable(
                        operation.variable_left, domain
                    )

        return domain

    def _apply_else_branch_condition(
        self, domain: IntervalDomain, conditions: List[Tuple[Union[Binary, Unary], bool]]
    ) -> IntervalDomain:
        """Apply inverse conditions when else branch is taken."""

        for operation, is_negated in conditions:
            if isinstance(operation, Unary):
                continue

            # Handle compound boolean operations
            if isinstance(operation, Binary) and operation.type in self.BOOLEAN_OPERATORS:
                if operation.type == BinaryType.OROR:
                    if is_negated:
                        # !(A || B) = !A && !B (can apply both negations - this is a conjunction)
                        # Let leaf conditions through
                        continue
                    else:
                        # (A || B) requires disjunction - skip

                        continue
                elif operation.type == BinaryType.ANDAND:
                    # Just skip, process leaf conditions
                    continue

            # Skip arithmetic operations - they are not conditions to be negated
            if operation.type in self.ARITHMETIC_OPERATORS:
                continue

            if isinstance(operation, Binary) and operation.type in self.COMPARISON_OPERATORS:
                # In else branch: the whole condition is FALSE
                # For negated operations: they were flipped by BANG, we want originals
                # For non-negated operations: we want them negated
                operator_to_apply = operation.type

                if is_negated:
                    # Was negated by BANG, use original (don't negate)
                    actual_comparison = operation
                else:
                    # Not negated, negate it for else branch
                    operator_to_apply = self._get_negated_operator(operation.type)

                    negated_result_variable = TemporaryVariable(operation.node)
                    negated_result_variable.set_type(operation.lvalue.type)

                    actual_comparison = Binary(
                        result=negated_result_variable,
                        left_variable=operation.variable_left,
                        right_variable=operation.variable_right,
                        operation_type=operator_to_apply,
                    )
                    actual_comparison.set_node(operation.node)

                # Verify the condition validity BEFORE applying
                if not self._condition_validity_checker.is_condition_valid(
                    actual_comparison, domain
                ):
                    logger.debug(
                        f"Condition {actual_comparison} is not valid, returning TOP (unreachable)"
                    )
                    return IntervalDomain.top()

                # Apply constraint to the actual variables in the comparison
                if operation.variable_left is not None:
                    left_operand_name = self._variable_info_manager.get_variable_name(
                        operation.variable_left
                    )
                    self._constraint_manager.store_variable_constraint(
                        left_operand_name, actual_comparison
                    )
                    self._constraint_manager.apply_constraint_from_variable(
                        operation.variable_left, domain
                    )

                    logger.debug(
                        f"After applying {actual_comparison}, domain for {left_operand_name}: {domain.state.get_range_variable(left_operand_name)}"
                    )

        return domain

    def _get_negated_operator(self, operator_type: BinaryType) -> BinaryType:
        """Get the negated version of a comparison operator."""
        negation_map = {
            BinaryType.GREATER: BinaryType.LESS_EQUAL,
            BinaryType.GREATER_EQUAL: BinaryType.LESS,
            BinaryType.LESS: BinaryType.GREATER_EQUAL,
            BinaryType.LESS_EQUAL: BinaryType.GREATER,
            BinaryType.EQUAL: BinaryType.NOT_EQUAL,
            BinaryType.NOT_EQUAL: BinaryType.EQUAL,
        }

        negated_operator = negation_map.get(operator_type)
        if negated_operator is None:
            logger.error(f"Cannot negate operation: {operator_type}")
            raise ValueError(f"Cannot negate operation: {operator_type}")

        return negated_operator

    def transfer_function(
        self,
        node: Node,
        domain: IntervalDomain,
        operation: Operation,
    ) -> None:
        self.transfer_function_helper(node, domain, operation)

    def transfer_function_helper(
        self,
        node: Node,
        domain: IntervalDomain,
        operation: Operation,
    ) -> None:

        if domain.variant == DomainVariant.TOP:
            return
        elif domain.variant == DomainVariant.BOTTOM:
            # Initialize domain from bottom with function parameters
            self._initialize_domain_from_bottom(node, domain)
            self._analyze_operation_by_type(operation, domain, node)
        elif domain.variant == DomainVariant.STATE:
            self._analyze_operation_by_type(operation, domain, node)

    def _analyze_operation_by_type(
        self,
        operation: Optional[Operation],
        domain: IntervalDomain,
        node: Node,
    ) -> None:
        """Route operation to appropriate handler based on type."""

        if self.node_declares_variable_without_initial_value(node):
            self._operation_handler.handle_uninitialized_variable(node, domain)

        if isinstance(operation, HighLevelCall):
            logger.debug(f"Processing HighLevelCall: {operation}")
            self._operation_handler.handle_high_level_call(node, domain, operation)

        if isinstance(operation, Index):
            logger.debug(f"Processing Index: {operation}")
            self._operation_handler.handle_index(node, domain, operation)

        if isinstance(operation, Assignment):
            logger.debug(f"Processing Assignment: {operation}")
            self._operation_handler.handle_assignment(node, domain, operation)

        if isinstance(operation, Binary):
            if operation.type in self.ARITHMETIC_OPERATORS:
                self._operation_handler.handle_arithmetic(node, domain, operation)
            elif operation.type in self.COMPARISON_OPERATORS:
                self._operation_handler.handle_comparison(node, domain, operation)
            elif operation.type in self.BOOLEAN_OPERATORS:
                self._operation_handler.handle_boolean(node, domain, operation)

        if isinstance(operation, SolidityCall):
            self._operation_handler.handle_solidity_call(node, domain, operation)

        if isinstance(operation, InternalCall):
            self._operation_handler.handle_internal_call(node, domain, operation, self)

        if isinstance(operation, LibraryCall):
            self._operation_handler.handle_library_call(node, domain, operation, self)

        if isinstance(operation, Member):
            self._operation_handler.handle_member(node, domain, operation)

        if isinstance(operation, Length):
            self._operation_handler.handle_length(node, domain, operation)

        if isinstance(operation, TypeConversion):
            self._operation_handler.handle_type_conversion(node, domain, operation)

        if isinstance(operation, Unary):
            self._operation_handler.handle_unary(node, domain, operation)

    def node_declares_variable_without_initial_value(self, node: Node) -> bool:
        """Check if the node has an uninitialized variable."""
        if not hasattr(node, "variable_declaration"):
            return False

        var = node.variable_declaration
        if var is None:
            return False

        # Check if variable has no initial value
        return not hasattr(var, "expression") or var.expression is None

    def _initialize_state_variable(
        self, state_variable, var_name: str, domain: IntervalDomain
    ) -> None:
        """Helper method to initialize a single state variable."""
        logger.debug(f"Initializing state variable: {var_name} with type {state_variable.type}")
        if isinstance(state_variable.type, ElementaryType):
            if self._variable_info_manager.is_type_numeric(state_variable.type):
                # Create interval range with type bounds
                interval_range = IntervalRange(
                    lower_bound=state_variable.type.min,
                    upper_bound=state_variable.type.max,
                )
                # Create range variable for the state variable
                range_variable = RangeVariable(
                    interval_ranges=[interval_range],
                    valid_values=None,
                    invalid_values=None,
                    var_type=state_variable.type,
                )
                # Add to domain state
                domain.state.add_range_variable(var_name, range_variable)
                logger.debug(f"Added numeric state variable {var_name} to domain state")
            elif self._variable_info_manager.is_type_bytes(state_variable.type):
                # Handle bytes state variables by creating offset and length variables
                range_variables = (
                    self._variable_info_manager.create_bytes_offset_and_length_variables(var_name)
                )
                # Add all created range variables to the domain state
                for nested_var_name, range_variable in range_variables.items():
                    domain.state.add_range_variable(nested_var_name, range_variable)
                    logger.debug(f"Added bytes state variable {nested_var_name} to domain state")
            else:
                # For any other type, create a placeholder
                placeholder = RangeVariable(
                    interval_ranges=[],
                    valid_values=ValueSet(set()),
                    invalid_values=ValueSet(set()),
                    var_type=state_variable.type,
                )
                domain.state.add_range_variable(var_name, placeholder)
                logger.debug(f"Added placeholder state variable {var_name} to domain state")
        elif isinstance(state_variable.type, UserDefinedType):
            if isinstance(state_variable.type.type, Contract):
                if state_variable.type.type.is_interface:
                    # Interface - create a placeholder
                    placeholder = RangeVariable(
                        interval_ranges=[],
                        valid_values=ValueSet(set()),
                        invalid_values=ValueSet(set()),
                        var_type=state_variable.type,
                    )
                    domain.state.add_range_variable(var_name, placeholder)
                else:
                    # Contract or Library - recursively initialize its state variables
                    for nested_state_var in state_variable.type.type.state_variables:
                        nested_var_name = f"{var_name}.{nested_state_var.name}"
                        self._initialize_state_variable(nested_state_var, nested_var_name, domain)
            else:
                # Handle actual struct state variables
                range_variables = self._variable_info_manager.create_struct_field_variables(
                    state_variable
                )
                # Add all created range variables to the domain state
                for nested_var_name, range_variable in range_variables.items():
                    domain.state.add_range_variable(nested_var_name, range_variable)

    def _initialize_domain_from_bottom(self, node: Node, domain: IntervalDomain) -> None:
        """Initialize domain state from bottom variant with function parameters, state variables, and constants."""
        logger.debug(f"Initializing domain from bottom for function: {node.function.name}")
        domain.variant = DomainVariant.STATE

        # Initialize function parameters and return variables
        self._initialize_function_parameters(node, domain)
        self._initialize_function_returns(node, domain)

        # Get the contract for this function
        contract = self._get_contract_for_function(node)

        # Initialize state variables for current contract and all inherited contracts
        if contract is not None:
            self._initialize_state_variables(contract, domain)
            # Initialize library constants
            self._initialize_library_constants(node, contract, domain)
        else:
            # For free functions, we don't have state variables or library constants
            logger.debug(
                f"Skipping state variables and library constants for free function {node.function.name}"
            )

        # Initialize msg.value for payable functions
        self._initialize_msg_value(node, domain)

        # Initialize all Solidity global variables
        self._initialize_solidity_globals(domain)

    def _get_contract_for_function(self, node: Node) -> Optional[Contract]:
        """Get the contract for the given function node, or None for free functions."""
        if isinstance(node.function, FunctionContract):
            contract = node.function.contract
            if not isinstance(contract, Contract):
                logger.error(f"Contract {contract.name} is not a valid contract")
                raise ValueError(f"Contract {contract.name} is not a valid contract")
            return contract
        elif isinstance(node.function, FunctionTopLevel):
            # Free functions don't belong to any contract
            logger.debug(f"Function {node.function.name} is a free function (top-level)")
            return None
        else:
            # For other function types, we need to handle them differently
            logger.error(
                f"Function {node.function.name} is not a contract function or free function"
            )
            raise ValueError(
                f"Function {node.function.name} is not a contract function or free function"
            )

    def _initialize_function_parameters(self, node: Node, domain: IntervalDomain) -> None:
        """Initialize function parameters in the domain state."""
        logger.debug(f"Initializing parameters for function: {node.function.name}")
        for parameter in node.function.parameters:
            logger.debug(
                f"Processing parameter: {parameter.canonical_name} with type {parameter.type} (type class: {type(parameter.type)})"
            )
            self._initialize_single_parameter(parameter, domain)

    def _initialize_single_parameter(self, parameter, domain: IntervalDomain) -> None:
        """Initialize a single parameter in the domain state."""
        # Resolve the actual type to process (handles type aliases)
        actual_type = self._resolve_parameter_type(parameter.type)

        if self._variable_info_manager.is_type_numeric(actual_type):
            self._initialize_numeric_parameter(parameter, actual_type, domain)
        elif self._variable_info_manager.is_type_bytes(actual_type):
            self._initialize_bytes_parameter(parameter, actual_type, domain)
        elif isinstance(parameter.type, ArrayType):
            self._initialize_array_parameter(parameter, domain)
        elif isinstance(parameter.type, UserDefinedType):
            self._initialize_user_defined_parameter(parameter, domain)
        else:
            # For other types (address, bool, string, etc.), create a placeholder
            self._create_placeholder_parameter(parameter, domain)

    def _resolve_parameter_type(self, param_type):
        """Resolve the actual type to process, handling type aliases."""
        if isinstance(param_type, TypeAliasTopLevel):
            return param_type.type
        elif isinstance(param_type, UserDefinedType) and isinstance(param_type.type, TypeAlias):
            return param_type.type.type
        else:
            return param_type

    def _initialize_numeric_parameter(self, parameter, actual_type, domain: IntervalDomain) -> None:
        """Initialize a numeric parameter with interval ranges."""
        interval_range = IntervalRange(
            lower_bound=actual_type.min,
            upper_bound=actual_type.max,
        )
        range_variable = RangeVariable(
            interval_ranges=[interval_range],
            valid_values=None,
            invalid_values=None,
            var_type=parameter.type,  # Keep original type for consistency
        )
        domain.state.add_range_variable(parameter.canonical_name, range_variable)
        logger.debug(f"Added numeric parameter {parameter.canonical_name} to domain state")

    def _initialize_bytes_parameter(self, parameter, actual_type, domain: IntervalDomain) -> None:
        """Initialize a bytes parameter with offset and length variables."""
        range_variables = self._variable_info_manager.create_bytes_offset_and_length_variables(
            parameter.canonical_name
        )
        for var_name, range_variable in range_variables.items():
            domain.state.add_range_variable(var_name, range_variable)
        logger.debug(f"Added bytes parameter {parameter.canonical_name} to domain state")

    def _initialize_array_parameter(self, parameter, domain: IntervalDomain) -> None:
        """Initialize an array parameter with a placeholder."""
        logger.debug(
            f"Processing ArrayType parameter: {parameter.canonical_name} with type {parameter.type}"
        )
        self._create_placeholder_parameter(parameter, domain)
        logger.debug(f"Added ArrayType parameter {parameter.canonical_name} to domain state")

    def _initialize_user_defined_parameter(self, parameter, domain: IntervalDomain) -> None:
        """Initialize a UserDefinedType parameter (struct, contract, interface, or type alias)."""
        logger.debug(
            f"Processing UserDefinedType parameter: {parameter.canonical_name} with type {parameter.type}"
        )

        # Check if it's a type alias wrapped in UserDefinedType
        if isinstance(parameter.type.type, TypeAlias):
            logger.debug(
                f"Processing TypeAlias parameter: {parameter.canonical_name} with underlying type {parameter.type.type.type}"
            )
            actual_type = parameter.type.type.type
            if self._variable_info_manager.is_type_numeric(actual_type):
                self._initialize_numeric_parameter(parameter, actual_type, domain)
            elif self._variable_info_manager.is_type_bytes(actual_type):
                self._initialize_bytes_parameter(parameter, actual_type, domain)
            else:
                self._create_placeholder_parameter(parameter, domain)
            return

        # Check if it's an interface
        if isinstance(parameter.type.type, Contract) and parameter.type.type.is_interface:
            logger.debug(
                f"Creating placeholder for interface parameter: {parameter.canonical_name}"
            )
            self._create_placeholder_parameter(parameter, domain)
            return

        # Handle structs and contracts by creating field variables
        range_variables = self._variable_info_manager.create_struct_field_variables(parameter)
        logger.debug(
            f"Created {len(range_variables)} range variables for UserDefinedType parameter"
        )

        # Add all created range variables to the domain state
        for var_name, range_variable in range_variables.items():
            domain.state.add_range_variable(var_name, range_variable)
            logger.debug(f"Added UserDefinedType parameter {var_name} to domain state")

        # Also create a placeholder variable for the parameter itself
        # This is needed for contract types and struct types to ensure the main parameter
        # (e.g., newModule_) is available in the domain state
        self._create_placeholder_parameter(parameter, domain)
        logger.debug(
            f"Added placeholder for UserDefinedType parameter {parameter.canonical_name} to domain state"
        )

    def _create_placeholder_parameter(self, parameter, domain: IntervalDomain) -> None:
        """Create a placeholder range variable for a parameter."""
        placeholder = RangeVariable(
            interval_ranges=[],
            valid_values=ValueSet(set()),
            invalid_values=ValueSet(set()),
            var_type=parameter.type,
        )
        domain.state.add_range_variable(parameter.canonical_name, placeholder)
        logger.debug(f"Added placeholder parameter {parameter.canonical_name} to domain state")

    def _initialize_function_returns(self, node: Node, domain: IntervalDomain) -> None:
        """Initialize function return variables in the domain state."""
        for return_var in node.function.returns:
            if isinstance(return_var.type, ElementaryType):
                if self._variable_info_manager.is_type_numeric(return_var.type):
                    # Create interval range with type bounds
                    interval_range = IntervalRange(
                        lower_bound=return_var.type.min,
                        upper_bound=return_var.type.max,
                    )
                    # Create range variable for the return variable
                    range_variable = RangeVariable(
                        interval_ranges=[interval_range],
                        valid_values=None,
                        invalid_values=None,
                        var_type=return_var.type,
                    )
                    # Add to domain state
                    domain.state.add_range_variable(return_var.canonical_name, range_variable)
                elif self._variable_info_manager.is_type_bytes(return_var.type):
                    # Handle bytes return variables by creating offset and length variables
                    range_variables = (
                        self._variable_info_manager.create_bytes_offset_and_length_variables(
                            return_var.canonical_name
                        )
                    )
                    # Add all created range variables to the domain state
                    for var_name, range_variable in range_variables.items():
                        domain.state.add_range_variable(var_name, range_variable)
                else:
                    # For any other type, create a placeholder
                    placeholder = RangeVariable(
                        interval_ranges=[],
                        valid_values=ValueSet(set()),
                        invalid_values=ValueSet(set()),
                        var_type=return_var.type,
                    )
                    domain.state.add_range_variable(return_var.canonical_name, placeholder)

            elif isinstance(return_var.type, UserDefinedType):
                # Handle struct return variables by creating field variables
                range_variables = self._variable_info_manager.create_struct_field_variables(
                    return_var
                )
                # Add all created range variables to the domain state
                for var_name, range_variable in range_variables.items():
                    domain.state.add_range_variable(var_name, range_variable)

    def _initialize_state_variables(self, contract: Contract, domain: IntervalDomain) -> None:
        """Initialize state variables for the contract and all inherited contracts."""
        logger.debug(f"Initializing state variables for contract: {contract.name}")

        # Get all contracts in the inheritance chain (including self)
        contracts_to_process = [contract]
        if hasattr(contract, "inheritance") and contract.inheritance:
            contracts_to_process.extend(contract.inheritance)

        logger.debug(f"Processing inheritance chain: {[c.name for c in contracts_to_process]}")

        for contract_to_process in contracts_to_process:
            logger.debug(f"Initializing state variables for contract: {contract_to_process.name}")
            for state_variable in contract_to_process.state_variables:
                logger.debug(
                    f"Processing state variable: {state_variable.canonical_name} with type {state_variable.type}"
                )
                self._initialize_state_variable(
                    state_variable, state_variable.canonical_name, domain
                )

    def _initialize_library_constants(
        self, node: Node, contract: Contract, domain: IntervalDomain
    ) -> None:
        """Initialize library constants for all libraries called by this function."""
        # Get all libraries called by this function
        all_libraries = set()

        # Add the current contract if it's a library
        if contract.is_library:
            all_libraries.add(contract)

        # Find all libraries called by this function
        for library_call in node.function.all_library_calls():
            if hasattr(library_call, "destination") and library_call.destination.is_library:
                all_libraries.add(library_call.destination)

        # Initialize constants for all libraries
        total_constants_found = 0
        for lib_contract in all_libraries:
            constants_found = 0
            for var_name, state_variable in lib_contract.variables_as_dict.items():
                if state_variable.is_constant and isinstance(state_variable.type, ElementaryType):
                    constants_found += 1
                    total_constants_found += 1
                    if self._variable_info_manager.is_type_numeric(state_variable.type):
                        # For constants, we know their exact value, so we create a range variable
                        # with the exact value in valid_values instead of a range
                        constant_value = None
                        if state_variable.expression:
                            # Handle different types of constant expressions
                            from slither.core.expressions.literal import Literal
                            from slither.core.expressions.unary_operation import UnaryOperation
                            from slither.utils.integer_conversion import convert_string_to_int

                            if isinstance(state_variable.expression, Literal):
                                constant_value = convert_string_to_int(
                                    state_variable.expression.converted_value
                                )
                            elif isinstance(state_variable.expression, UnaryOperation):
                                constant_value = convert_string_to_int(
                                    str(state_variable.expression).replace(" ", "")
                                )
                            else:
                                # For other expression types, try to convert to int
                                try:
                                    constant_value = convert_string_to_int(
                                        str(state_variable.expression)
                                    )
                                except:
                                    # If conversion fails, use the type bounds
                                    constant_value = None

                        if constant_value is not None:
                            # Create range variable with exact constant value
                            range_variable = RangeVariable(
                                interval_ranges=[],
                                valid_values=ValueSet([constant_value]),
                                invalid_values=None,
                                var_type=state_variable.type,
                            )
                        else:
                            # Fallback to type bounds if we can't determine the exact value
                            interval_range = IntervalRange(
                                lower_bound=state_variable.type.min,
                                upper_bound=state_variable.type.max,
                            )
                            range_variable = RangeVariable(
                                interval_ranges=[interval_range],
                                valid_values=None,
                                invalid_values=None,
                                var_type=state_variable.type,
                            )

                        # Add to domain state
                        domain.state.add_range_variable(
                            state_variable.canonical_name, range_variable
                        )
                    elif self._variable_info_manager.is_type_bytes(state_variable.type):
                        # Handle bytes constants by creating offset and length variables
                        range_variables = (
                            self._variable_info_manager.create_bytes_offset_and_length_variables(
                                state_variable.canonical_name
                            )
                        )
                        # Add all created range variables to the domain state
                        for var_name_bytes, range_variable in range_variables.items():
                            domain.state.add_range_variable(var_name_bytes, range_variable)

    def _initialize_msg_value(self, node: Node, domain: IntervalDomain) -> None:
        """Initialize msg.value for payable functions."""
        # Only contract functions can be payable, free functions cannot
        if isinstance(node.function, FunctionContract) and node.function.payable:
            msg_value_type = ElementaryType("uint256")
            interval_range = IntervalRange(
                lower_bound=msg_value_type.min,
                upper_bound=msg_value_type.max,
            )
            msg_value_range_variable = RangeVariable(
                interval_ranges=[interval_range],
                valid_values=None,
                invalid_values=None,
                var_type=msg_value_type,
            )
            domain.state.add_range_variable("msg.value", msg_value_range_variable)

    def _initialize_solidity_globals(self, domain: IntervalDomain) -> None:
        """Initialize all Solidity global variables in the domain state."""
        # Block properties
        solidity_globals = {
            # Block properties (uint256)
            "block.basefee": {
                "type": ElementaryType("uint256"),
                "range": (Decimal("0"), Decimal("1000000000000")),  # 0 to 1000 gwei
            },
            "block.blobbasefee": {
                "type": ElementaryType("uint256"),
                "range": (Decimal("0"), Decimal("1000000000000")),  # 0 to 1000 gwei
            },
            "block.chainid": {
                "type": ElementaryType("uint256"),
                "range": (Decimal("1"), Decimal("4294967295")),  # 1 to 2^32 - 1
            },
            "block.difficulty": {
                "type": ElementaryType("uint256"),
                "range": (Decimal("0"), Decimal("100000000000000000000")),  # Large but reasonable
            },
            "block.gaslimit": {
                "type": ElementaryType("uint256"),
                "range": (Decimal("1000000"), Decimal("50000000")),  # 1M to 50M
            },
            "block.number": {
                "type": ElementaryType("uint256"),
                "range": (Decimal("0"), Decimal("100000000")),  # 0 to 100M blocks
            },
            "block.prevrandao": {
                "type": ElementaryType("uint256"),
                "range": (
                    Decimal("0"),
                    Decimal(
                        "115792089237316195423570985008687907853269984665640564039457584007913129639935"
                    ),
                ),  # Full uint256
            },
            "block.timestamp": {
                "type": ElementaryType("uint256"),
                "range": (Decimal("0"), Decimal("4102444800")),  # 0 to year 2100
            },
            # Message properties
            "msg.value": {
                "type": ElementaryType("uint256"),
                "range": (Decimal("0"), Decimal("1000000000000000000000")),  # 0 to 1000 ETH in wei
            },
            # Transaction properties
            "tx.gasprice": {
                "type": ElementaryType("uint256"),
                "range": (Decimal("0"), Decimal("1000000000000")),  # 0 to 1000 gwei
            },
            # Gas-related globals
            "msg.gas": {
                "type": ElementaryType("uint256"),
                "range": (Decimal("0"), Decimal("50000000")),  # 0 to block gas limit
            },
            "gasleft": {
                "type": ElementaryType("uint256"),
                "range": (Decimal("0"), Decimal("50000000")),  # 0 to block gas limit
            },
            # Backward compatibility
            "timestamp": {
                "type": ElementaryType("uint256"),
                "range": (Decimal("0"), Decimal("4102444800")),  # 0 to year 2100
            },
        }

        # Add address type globals
        address_globals = ["block.coinbase", "msg.sender", "tx.origin"]
        for var_name in address_globals:
            address_type = ElementaryType("address")
            range_variable = RangeVariable(
                interval_ranges=[],  # No specific intervals for address
                valid_values=ValueSet(set()),
                invalid_values=ValueSet(set()),
                var_type=address_type,
            )
            domain.state.add_range_variable(var_name, range_variable)

        # Add bytes type globals
        bytes_globals = {
            "msg.data": "bytes",
            "msg.sig": "bytes4",
        }
        for var_name, type_name in bytes_globals.items():
            bytes_type = ElementaryType(type_name)
            range_variable = RangeVariable(
                interval_ranges=[],  # No intervals for bytes
                valid_values=ValueSet(set()),
                invalid_values=ValueSet(set()),
                var_type=bytes_type,
            )
            domain.state.add_range_variable(var_name, range_variable)

        # Add uint256 globals with specific ranges
        for var_name, config in solidity_globals.items():
            var_type = config["type"]
            min_val, max_val = config["range"]

            range_variable = RangeVariable(
                interval_ranges=[IntervalRange(min_val, max_val)],
                valid_values=ValueSet(set()),
                invalid_values=ValueSet(set()),
                var_type=var_type,
            )
            domain.state.add_range_variable(var_name, range_variable)

        logger.debug("Initialized all Solidity global variables in domain state")

    def apply_widening(
        self, current_state: IntervalDomain, previous_state: IntervalDomain, widening_literals: set
    ) -> IntervalDomain:
        """Apply widening operations to the current state."""
        return self._widening.apply_widening(current_state, previous_state, widening_literals)
