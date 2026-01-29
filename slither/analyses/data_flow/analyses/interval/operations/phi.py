"""Handler for Phi operations (SSA merge points)."""

from typing import Optional, TYPE_CHECKING

from slither.analyses.data_flow.analyses.interval.operations.base import BaseOperationHandler
from slither.analyses.data_flow.analyses.interval.utils import IntervalSMTUtils
from slither.analyses.data_flow.smt_solver.types import SMTTerm
from slither.core.solidity_types.elementary_type import ElementaryType
from slither.slithir.operations.phi import Phi

if TYPE_CHECKING:
    from slither.analyses.data_flow.analyses.interval.analysis.domain import IntervalDomain
    from slither.analyses.data_flow.analyses.interval.core.tracked_variable import (
        TrackedSMTVariable,
    )
    from slither.core.cfg.node import Node


class PhiHandler(BaseOperationHandler):
    """Handler for Phi operations (merges values from different branches)."""

    # Class-level set to track which Phi lvalues have been constrained (reset per analysis)
    _applied_phi_constraints: set[str] = set()

    @classmethod
    def reset_applied_constraints(cls) -> None:
        """Reset the set of applied Phi constraints (call at start of analysis)."""
        cls._applied_phi_constraints = set()

    def handle(
        self,
        operation: Optional[Phi],
        domain: "IntervalDomain",
        node: "Node",
    ) -> None:
        """Handle Phi operation by creating OR constraint for merged values."""
        if operation is None or self.solver is None:
            return

        # Try to detect constant branch conditions for path-sensitive phi handling
        branch_info = self._analyze_branch_condition(node, domain)

        lvalue_var = self._get_or_create_lvalue_variable(operation.lvalue, domain)

        # Always try to propagate struct member fields, even if base Phi is skipped (for struct types)
        self._propagate_struct_members(operation.lvalue, operation.rvalues, domain)

        # If lvalue is not an elementary type (e.g., struct), skip the base Phi constraint
        if lvalue_var is None:
            return

        lvalue_name = lvalue_var.base.name

        # Skip if we've already applied constraint for this Phi
        if lvalue_name in PhiHandler._applied_phi_constraints:
            return

        # Check if all rvalues exist in domain - if not, skip (will be processed again later)
        all_rvalues_exist = self._all_rvalues_exist_check(operation.rvalues, domain, lvalue_name)
        if not all_rvalues_exist:
            self.logger.debug(
                "Skipping Phi constraint for '{lvalue}' - not all rvalues exist yet",
                lvalue=lvalue_name,
            )
            return

        or_constraints = self._collect_phi_constraints(
            lvalue_var, operation.rvalues, domain, node, branch_info
        )
        if not or_constraints:
            return

        self._apply_phi_constraint(lvalue_var, or_constraints, operation.rvalues)

        # Mark this Phi as applied
        PhiHandler._applied_phi_constraints.add(lvalue_name)

    def _all_rvalues_exist_check(
        self,
        rvalues: list[object],
        domain: "IntervalDomain",
        lvalue_name: str,
    ) -> bool:
        """Check if all rvalues exist in the domain state.

        Also checks if enough SSA versions exist to ensure we have all branches covered.
        """
        rvalue_names_found = []

        for rvalue in rvalues:
            rvalue_name = IntervalSMTUtils.resolve_variable_name(rvalue)
            if rvalue_name is None:
                return False
            # Input parameters (_0, _1) always exist, check for others
            if self._is_input_param_version(rvalue_name, domain):
                continue
            rvalue_var = IntervalSMTUtils.get_tracked_variable(domain, rvalue_name)
            if rvalue_var is None:
                # Try to materialize missing constant versions for state variables (e.g., _BASE_POINTS_3)
                rvalue_var = self._materialize_missing_constant_version(rvalue_name, domain)
                if rvalue_var is None:
                    return False
            rvalue_names_found.append(rvalue_name)

        # Additional check: make sure we have enough SSA versions
        # If there's only 1 non-input rvalue:
        # - Accept immediately when the Phi has only one rvalue (e.g., constant/state initializer)
        # - Otherwise keep the conservative wait for more concrete versions
        if len(rvalue_names_found) <= 1:
            if len(rvalues) == 1:
                return True

            # Get base variable name for checking other versions
            base_name = self._get_base_name(lvalue_name)

            if base_name:
                # Count how many versions exist (excluding input params and lvalue)
                version_count = 0
                all_vars = list(domain.state.get_range_variables().keys())
                for var_name in all_vars:
                    # Skip the lvalue itself
                    if var_name == lvalue_name:
                        continue
                    if var_name.startswith(base_name + "_"):
                        ssa_num = self._get_ssa_num(var_name)
                        if ssa_num >= 2:  # Not input param
                            version_count += 1

                # Wait for at least 2 concrete versions (typical for if-else branches)
                if version_count < 2:
                    return False

        return True

    def _get_or_create_lvalue_variable(
        self, lvalue: object, domain: "IntervalDomain"
    ) -> Optional["TrackedSMTVariable"]:
        """Get or create tracked variable for Phi lvalue."""
        lvalue_name = IntervalSMTUtils.resolve_variable_name(lvalue)
        if lvalue_name is None:
            return None

        lvalue_type = IntervalSMTUtils.resolve_elementary_type(getattr(lvalue, "type", None))
        if lvalue_type is None:
            self.logger.debug("Unsupported lvalue type for Phi operation; skipping.")
            return None

        lvalue_var = IntervalSMTUtils.get_tracked_variable(domain, lvalue_name)
        if lvalue_var is None:
            lvalue_var = IntervalSMTUtils.create_tracked_variable(
                self.solver, lvalue_name, lvalue_type
            )
            if lvalue_var is None:
                return None
            domain.state.set_range_variable(lvalue_name, lvalue_var)

        return lvalue_var

    def _collect_phi_constraints(
        self,
        lvalue_var: "TrackedSMTVariable",
        rvalues: list[object],
        domain: "IntervalDomain",
        node: "Node" = None,
        branch_info: Optional[dict] = None,
    ) -> list[SMTTerm]:
        """Collect equality constraints for each rvalue in Phi operation.

        Also checks for missing SSA versions that should be included (workaround for SSA bugs).

        If branch_info is provided with a known condition_value, uses path-sensitive
        phi handling to only include rvalues from reachable branches.
        """
        or_constraints: list[SMTTerm] = []
        lvalue_name = lvalue_var.base.name
        used_rvalue_names: set[str] = set()
        rvalue_names_from_ssa: set[str] = set()

        # Build mapping from rvalue to defining node (for path-sensitive analysis)
        rvalue_to_father: dict[str, "Node"] = {}
        if branch_info and node:
            rvalue_to_father = self._map_rvalues_to_fathers(rvalues, node)

        # First, collect rvalue names from the SSA Phi
        for rvalue in rvalues:
            rvalue_name = IntervalSMTUtils.resolve_variable_name(rvalue)
            if rvalue_name:
                rvalue_names_from_ssa.add(rvalue_name)

        # Find missing SSA versions first to determine if input param should be excluded
        missing_versions = self._find_missing_phi_rvalues(
            lvalue_name, rvalue_names_from_ssa, domain
        )

        # Check if we should exclude input parameter (version _1)
        # If there are concrete assignment versions, the input shouldn't flow through
        should_exclude_input = self._should_exclude_input_param(
            lvalue_name, rvalue_names_from_ssa, missing_versions, domain
        )

        # Collect constraints from explicit rvalues (excluding input if needed)
        for rvalue in rvalues:
            rvalue_name = IntervalSMTUtils.resolve_variable_name(rvalue)
            if rvalue_name is None:
                continue

            # Skip input parameter if we determined it shouldn't be included
            if should_exclude_input and self._is_input_param_version(rvalue_name, domain):
                self.logger.debug(
                    "Excluding input param '{rvalue_name}' from Phi (all branches assign)",
                    rvalue_name=rvalue_name,
                )
                continue

            # Path-sensitive filtering: skip rvalues from unreachable branches
            if branch_info and branch_info.get('condition_value') is not None:
                condition_value = branch_info['condition_value']
                father = rvalue_to_father.get(rvalue_name)
                if father is not None:
                    true_father = branch_info.get('true_branch_father')
                    false_father = branch_info.get('false_branch_father')

                    # If condition is always True, skip rvalues from false branch
                    if condition_value is True and father == false_father:
                        self.logger.debug(
                            "Excluding '{rvalue_name}' from Phi (unreachable false branch)",
                            rvalue_name=rvalue_name,
                        )
                        continue
                    # If condition is always False, skip rvalues from true branch
                    if condition_value is False and father == true_father:
                        self.logger.debug(
                            "Excluding '{rvalue_name}' from Phi (unreachable true branch)",
                            rvalue_name=rvalue_name,
                        )
                        continue

            rvalue_var = IntervalSMTUtils.get_tracked_variable(domain, rvalue_name)
            if rvalue_var is None:
                self.logger.debug(
                    "Rvalue '{rvalue_name}' not found in domain for Phi operation",
                    rvalue_name=rvalue_name,
                )
                continue

            constraint = self._create_equality_constraint(lvalue_var, rvalue_var)
            if constraint is not None:
                or_constraints.append(constraint)
                used_rvalue_names.add(rvalue_name)

        # Add missing SSA versions
        for rvalue_name in missing_versions:
            if rvalue_name in used_rvalue_names:
                continue
            rvalue_var = IntervalSMTUtils.get_tracked_variable(domain, rvalue_name)
            if rvalue_var is None:
                continue
            constraint = self._create_equality_constraint(lvalue_var, rvalue_var)
            if constraint is not None:
                or_constraints.append(constraint)
                self.logger.debug(
                    "Added missing SSA version '{rvalue_name}' to Phi for '{lvalue_name}'",
                    rvalue_name=rvalue_name,
                    lvalue_name=lvalue_name,
                )

        return or_constraints

    def _map_rvalues_to_fathers(
        self,
        rvalues: list[object],
        phi_node: "Node",
    ) -> dict[str, "Node"]:
        """Map each rvalue name to the father node where it was defined.

        This is used for path-sensitive phi handling to determine which branch
        each rvalue comes from.
        """
        result: dict[str, "Node"] = {}

        for father in phi_node.fathers:
            # Check each IR in the father node to find variable assignments
            for ir in father.irs_ssa or []:
                # Look for assignment operations that define variables
                if hasattr(ir, 'lvalue') and ir.lvalue is not None:
                    lvalue_name = IntervalSMTUtils.resolve_variable_name(ir.lvalue)
                    if lvalue_name:
                        # Check if this matches any rvalue
                        for rvalue in rvalues:
                            rvalue_name = IntervalSMTUtils.resolve_variable_name(rvalue)
                            if rvalue_name == lvalue_name:
                                result[rvalue_name] = father
                                break

        return result

    def _is_input_param_version(self, var_name: str, domain: "IntervalDomain" = None) -> bool:
        """Check if this is an input parameter version (function param, ends with _0 or _1).

        Only considers variables that are function parameters (not local var first assignments).
        """
        if "_" not in var_name:
            return False
        suffix = var_name.rsplit("_", 1)[-1]
        if suffix not in ("0", "1"):
            return False

        # If we have domain access, check if _0 version exists (indicates local var, not param)
        # Function params typically have _1 as their first version with no _0
        if domain is not None:
            base_name = self._get_base_name(var_name)
            if base_name:
                # If there's a _0 version, this is a local var (initialized to default)
                zero_version = base_name + "_0"
                if domain.state.has_range_variable(zero_version):
                    return False

        return True

    def _should_exclude_input_param(
        self,
        lvalue_name: str,
        rvalue_names: set[str],
        missing_versions: list[str],
        domain: "IntervalDomain",
    ) -> bool:
        """Determine if input parameter should be excluded from Phi.

        Returns True if all branches appear to assign to the variable (i.e., we have
        concrete assignment versions like _2, _3, _4, not just the input _1).
        """
        # Extract base name for matching
        base_name = self._get_base_name(lvalue_name)
        if not base_name:
            return False

        # Check if we have any concrete assignment versions (SSA >= 2)
        has_concrete_assignment = False
        for version in list(rvalue_names) + missing_versions:
            ssa_num = self._get_ssa_num(version)
            if ssa_num >= 2:
                has_concrete_assignment = True
                break

        # If we have concrete assignments and the rvalues include input param, likely SSA bug
        if has_concrete_assignment:
            for rv in rvalue_names:
                if self._is_input_param_version(rv, domain):
                    return True

        return False

    def _materialize_missing_constant_version(
        self, rvalue_name: str, domain: "IntervalDomain"
    ) -> Optional["TrackedSMTVariable"]:
        """Create a missing SSA version for constant/state variables by cloning an existing version."""
        # Guard: need base name to search for sibling versions
        base_name = self._get_base_name(rvalue_name)
        if base_name is None:
            return None

        # Find an existing version (prefer _0, then _1, then any earlier SSA) to clone from
        candidate_sources = []
        for var_name in domain.state.get_range_variables().keys():
            if not var_name.startswith(base_name + "_"):
                continue
            try:
                ssa_num = self._get_ssa_num(var_name)
            except Exception:
                continue
            candidate_sources.append((ssa_num, var_name))

        if not candidate_sources:
            return None

        # Prefer the lowest SSA version (constant initializer) as source
        candidate_sources.sort(key=lambda item: item[0])
        _, source_name = candidate_sources[0]

        source_var = IntervalSMTUtils.get_tracked_variable(domain, source_name)
        if source_var is None:
            return None

        type_str = source_var.base.metadata.get("solidity_type")
        if not type_str:
            return None

        try:
            source_type = ElementaryType(type_str)
        except Exception:
            return None

        # Create the missing version with the same type and constrain it to the source value
        target_var = IntervalSMTUtils.create_tracked_variable(self.solver, rvalue_name, source_type)
        if target_var is None:
            return None

        domain.state.set_range_variable(rvalue_name, target_var)
        self.solver.assert_constraint(target_var.term == source_var.term)
        target_var.assert_no_overflow(self.solver)
        return target_var

    def _get_base_name(self, var_name: str) -> Optional[str]:
        """Extract base variable name without SSA suffix."""
        if "|" in var_name and "_" in var_name:
            parts = var_name.rsplit("|", 1)
            prefix = parts[0]
            ssa_part = parts[1]
            if "_" in ssa_part:
                base_var_name = ssa_part.rsplit("_", 1)[0]
                return f"{prefix}|{base_var_name}"
        return None

    def _find_missing_phi_rvalues(
        self,
        lvalue_name: str,
        used_rvalue_names: set[str],
        domain: "IntervalDomain",
    ) -> list[str]:
        """Find SSA versions of the same variable that should be in the Phi but weren't listed.

        This works around Slither SSA bugs where nested if-else results aren't included.
        """
        # Extract base variable name (before SSA suffix like _6)
        # Format: "Contract.func().var|var_6" → extract "var" to find "var_5", "var_4", etc.
        base_name = lvalue_name
        lvalue_ssa_num = -1

        # Handle the "|var_N" suffix format
        if "|" in lvalue_name:
            parts = lvalue_name.rsplit("|", 1)
            prefix = parts[0]  # "Contract.func().var"
            ssa_part = parts[1]  # "var_6"

            # Extract SSA number from the ssa_part
            if "_" in ssa_part:
                base_var_name, ssa_num_str = ssa_part.rsplit("_", 1)
                try:
                    lvalue_ssa_num = int(ssa_num_str)
                    base_name = f"{prefix}|{base_var_name}"
                except ValueError:
                    return []
            else:
                return []
        else:
            return []

        # Look for other SSA versions in the domain that we haven't used
        missing: list[str] = []
        all_var_names = domain.state.get_range_variables().keys()

        for var_name in all_var_names:
            # Skip if already used
            if var_name in used_rvalue_names:
                continue
            # Skip the lvalue itself
            if var_name == lvalue_name:
                continue

            # Check if this is another SSA version of the same variable
            if var_name.startswith(base_name + "_"):
                suffix = var_name[len(base_name) + 1 :]
                try:
                    ssa_num = int(suffix)
                    # Only include versions less than lvalue (predecessors in SSA)
                    # but greater than the minimum used (to catch nested results like variable_5)
                    if ssa_num < lvalue_ssa_num:
                        # Check if there's a used version with lower number
                        # If so, we might need this version (nested if-else result)
                        has_lower_used = any(
                            self._get_ssa_num(used) < ssa_num
                            for used in used_rvalue_names
                            if used.startswith(base_name + "_")
                        )
                        if has_lower_used:
                            missing.append(var_name)
                except ValueError:
                    continue

        return missing

    def _get_ssa_num(self, var_name: str) -> int:
        """Extract SSA number from variable name."""
        if "_" in var_name:
            try:
                return int(var_name.rsplit("_", 1)[1])
            except ValueError:
                return -1
        return -1

    def _create_equality_constraint(
        self,
        lvalue_var: "TrackedSMTVariable",
        rvalue_var: "TrackedSMTVariable",
    ) -> Optional[SMTTerm]:
        """Create equality constraint between lvalue and rvalue, handling width mismatches."""
        lvalue_width = self.solver.bv_size(lvalue_var.term)
        rvalue_width = self.solver.bv_size(rvalue_var.term)

        if lvalue_width != rvalue_width:
            rvalue_term = rvalue_var.term
            if rvalue_width < lvalue_width:
                is_signed = bool(rvalue_var.base.metadata.get("is_signed", False))
                rvalue_term = IntervalSMTUtils.extend_to_width(
                    self.solver, rvalue_term, lvalue_width, is_signed
                )
            else:
                rvalue_term = IntervalSMTUtils.truncate_to_width(
                    self.solver, rvalue_term, lvalue_width
                )
            return lvalue_var.term == rvalue_term

        return lvalue_var.term == rvalue_var.term

    def _apply_phi_constraint(
        self,
        lvalue_var: "TrackedSMTVariable",
        or_constraints: list[SMTTerm],
        rvalues: list[object],
    ) -> None:
        """Apply OR constraint to solver and assert no overflow."""
        or_constraint: SMTTerm = self.solver.Or(*or_constraints)
        self.solver.assert_constraint(or_constraint)

        lvalue_var.assert_no_overflow(self.solver)

        lvalue_name = lvalue_var.base.name
        rvalue_names = ", ".join(
            IntervalSMTUtils.resolve_variable_name(rv) or "?" for rv in rvalues
        )
        self.logger.debug(
            "Phi operation: {lvalue_name} = phi({rvalue_names})",
            lvalue_name=lvalue_name,
            rvalue_names=rvalue_names,
        )

    def _get_explicit_constant_value(
        self,
        condition_var: "TrackedSMTVariable",
    ) -> Optional[bool]:
        """Check if the condition variable has an explicit constant value.

        Looks for direct equality constraints like `var == 0` or `var == 1`
        in the solver assertions. This is more reliable than satisfiability
        checks because it only considers explicit constraints, not derived
        constraints from overflow analysis.

        Returns:
            True if explicitly constrained to non-zero (true)
            False if explicitly constrained to zero (false)
            None if no explicit constant constraint found
        """
        if self.solver is None:
            return None

        term = condition_var.term
        term_str = str(term)

        # Look through solver assertions for explicit equality constraints
        for assertion in self.solver.get_assertions():
            # Check for direct equality: term == constant or constant == term
            if self.solver.is_eq_constraint(assertion):
                operands = self.solver.get_eq_operands(assertion)
                if operands is None:
                    continue
                lhs, rhs = operands
                lhs_str, rhs_str = str(lhs), str(rhs)

                # Check if LHS is our variable and RHS is a constant
                if lhs_str == term_str:
                    const_val = self.solver.get_constant_as_long(rhs)
                    if const_val is not None:
                        return const_val != 0

                # Check if RHS is our variable and LHS is a constant
                if rhs_str == term_str:
                    const_val = self.solver.get_constant_as_long(lhs)
                    if const_val is not None:
                        return const_val != 0

        return None

    def _analyze_branch_condition(
        self,
        node: "Node",
        domain: "IntervalDomain",
    ) -> Optional[dict]:
        """Analyze if the branch leading to this phi has a known constant condition.

        Returns dict with:
        - 'if_node': The IF node controlling the branch
        - 'condition_var': The condition variable name
        - 'condition_value': The constant value (True/False) if known, None otherwise
        - 'true_branch_father': The father node from the true branch
        - 'false_branch_father': The father node from the false branch

        Returns None if no constant condition can be determined.
        """
        if self.solver is None:
            return None

        # Find the common IF node ancestor
        if_node = None
        true_father = None
        false_father = None

        for father in node.fathers:
            for gfather in father.fathers:
                from slither.core.cfg.node import NodeType
                if gfather.type == NodeType.IF:
                    if_node = gfather
                    # Determine which branch this father came from
                    if len(gfather.sons) == 2:
                        if father == gfather.sons[0]:
                            true_father = father
                        elif father == gfather.sons[1]:
                            false_father = father
                    break

        if if_node is None:
            return None

        # Find the condition variable from the IF node
        condition_name = None
        for ir in if_node.irs_ssa or []:
            if hasattr(ir, 'value'):
                condition_name = IntervalSMTUtils.resolve_variable_name(ir.value)
                break

        if condition_name is None:
            return None

        # Get the condition variable from domain
        condition_var = IntervalSMTUtils.get_tracked_variable(domain, condition_name)
        if condition_var is None:
            return None

        # Check if condition has a known constant value by looking for explicit
        # equality constraints in the solver (e.g., from interprocedural analysis).
        # We avoid using satisfiability checks because the solver may contain
        # overflow constraints that make branches appear unreachable when they aren't.
        condition_value = self._get_explicit_constant_value(condition_var)

        return {
            'if_node': if_node,
            'condition_var': condition_name,
            'condition_value': condition_value,
            'true_branch_father': true_father,
            'false_branch_father': false_father,
        }

    def _propagate_struct_members(
        self,
        lvalue: object,
        rvalues: list[object],
        domain: "IntervalDomain",
    ) -> None:
        """Propagate struct member fields when merging struct variables through Phi."""
        if self.solver is None:
            return

        lvalue_name = IntervalSMTUtils.resolve_variable_name(lvalue)
        if lvalue_name is None:
            return

        # Find all struct member variables for the lvalue (e.g., "user_5.id", "user_5.balance")
        # First, get or create the lvalue member variables
        lvalue_base = lvalue_name.split("|")[0] if "|" in lvalue_name else lvalue_name

        # Find existing struct members from rvalues to determine which members exist
        # Use prefix index for fast lookup
        member_names: set[str] = set()

        for rvalue in rvalues:
            rvalue_name = IntervalSMTUtils.resolve_variable_name(rvalue)
            if rvalue_name is None:
                continue

            # Use prefix index to find struct member variables for this rvalue
            rvalue_prefix = f"{rvalue_name}."
            candidate_vars = domain.state.get_variables_by_prefix(rvalue_prefix)

            for var_name in candidate_vars:
                # Extract member name (everything after the prefix)
                member_name = var_name[len(rvalue_prefix):]
                member_names.add(member_name)
                self.logger.debug(
                    "Found struct member '{var_name}' matching rvalue '{rvalue}'",
                    var_name=var_name,
                    rvalue=rvalue_name,
                )

        if not member_names:
            return

        # For each struct member, create a Phi operation
        for member_name in member_names:
            lvalue_member_name = f"{lvalue_name}.{member_name}"

            # Get or create lvalue member variable
            lvalue_member_var = IntervalSMTUtils.get_tracked_variable(domain, lvalue_member_name)
            if lvalue_member_var is None:
                # Try to infer type from rvalue members
                member_type: Optional[ElementaryType] = None
                for rvalue in rvalues:
                    rvalue_name = IntervalSMTUtils.resolve_variable_name(rvalue)
                    if rvalue_name is None:
                        continue
                    rvalue_member_name = f"{rvalue_name}.{member_name}"
                    rvalue_member_var = IntervalSMTUtils.get_tracked_variable(
                        domain, rvalue_member_name
                    )
                    if rvalue_member_var is not None:
                        # Use the same type as the rvalue member
                        if hasattr(rvalue_member_var.base, "metadata"):
                            type_str = rvalue_member_var.base.metadata.get("solidity_type")
                            if type_str:
                                from slither.core.solidity_types.elementary_type import (
                                    ElementaryType,
                                )

                                member_type = ElementaryType(type_str)
                                break

                if member_type is None:
                    continue

                lvalue_member_var = IntervalSMTUtils.create_tracked_variable(
                    self.solver, lvalue_member_name, member_type
                )
                if lvalue_member_var is None:
                    continue
                domain.state.set_range_variable(lvalue_member_name, lvalue_member_var)
                lvalue_member_var.assert_no_overflow(self.solver)

            # Collect equality constraints for each rvalue member
            or_constraints: list[SMTTerm] = []
            for rvalue in rvalues:
                rvalue_name = IntervalSMTUtils.resolve_variable_name(rvalue)
                if rvalue_name is None:
                    continue

                rvalue_member_name = f"{rvalue_name}.{member_name}"
                rvalue_member_var = IntervalSMTUtils.get_tracked_variable(
                    domain, rvalue_member_name
                )

                # Also try with base name in case of SSA version differences
                if rvalue_member_var is None:
                    rvalue_base = rvalue_name.split("|")[0] if "|" in rvalue_name else rvalue_name
                    alt_rvalue_member_name = f"{rvalue_base}.{member_name}"
                    rvalue_member_var = IntervalSMTUtils.get_tracked_variable(
                        domain, alt_rvalue_member_name
                    )

                if rvalue_member_var is None:
                    continue

                # Create equality constraint
                constraint = self._create_equality_constraint(lvalue_member_var, rvalue_member_var)
                if constraint is not None:
                    or_constraints.append(constraint)

            # Apply OR constraint for this struct member
            if or_constraints:
                if len(or_constraints) == 1:
                    # Single constraint, use direct equality
                    self.solver.assert_constraint(or_constraints[0])
                else:
                    # Multiple constraints, use OR
                    or_constraint: SMTTerm = self.solver.Or(*or_constraints)
                    self.solver.assert_constraint(or_constraint)

                self.logger.debug(
                    "Propagated struct member '{lvalue_member}' through Phi from {count} rvalue(s)",
                    lvalue_member=lvalue_member_name,
                    count=len(or_constraints),
                )
