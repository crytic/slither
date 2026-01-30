"""Handler for Phi operations (SSA merge points)."""

from dataclasses import dataclass
from typing import Optional, TYPE_CHECKING

from slither.analyses.data_flow.analyses.interval.operations.base import BaseOperationHandler
from slither.analyses.data_flow.analyses.interval.utils import IntervalSMTUtils
from slither.analyses.data_flow.analyses.interval.core.tracked_variable import TrackedSMTVariable
from slither.analyses.data_flow.smt_solver.types import SMTTerm
from slither.core.solidity_types.elementary_type import ElementaryType
from slither.slithir.operations.phi import Phi

if TYPE_CHECKING:
    from slither.analyses.data_flow.analyses.interval.analysis.domain import IntervalDomain
    from slither.core.cfg.node import Node


@dataclass
class PhiContext:
    """Context for phi operation handling."""

    domain: "IntervalDomain"
    branch_info: Optional[dict]
    rvalue_to_father: dict[str, "Node"]
    should_exclude_input: bool


@dataclass
class PhiConstraintsState:
    """State accumulated during phi constraint building."""

    or_constraints: list[SMTTerm]
    used_names: set[str]


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

        # Always try to propagate struct member fields, even if base Phi is skipped
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
        """Check if all rvalues exist in the domain state."""
        rvalue_names_found = self._collect_existing_rvalues(rvalues, domain)
        if rvalue_names_found is None:
            return False

        if len(rvalue_names_found) <= 1:
            return self._check_sufficient_versions(rvalues, lvalue_name, domain)

        return True

    def _collect_existing_rvalues(
        self, rvalues: list[object], domain: "IntervalDomain"
    ) -> Optional[list[str]]:
        """Collect rvalue names that exist in domain. Returns None if any missing."""
        names_found = []
        for rvalue in rvalues:
            rvalue_name = IntervalSMTUtils.resolve_variable_name(rvalue)
            if rvalue_name is None:
                return None
            if self._is_input_param_version(rvalue_name, domain):
                continue
            if not self._ensure_rvalue_exists(rvalue_name, domain):
                return None
            names_found.append(rvalue_name)
        return names_found

    def _ensure_rvalue_exists(self, rvalue_name: str, domain: "IntervalDomain") -> bool:
        """Ensure rvalue exists, materializing if needed."""
        rvalue_var = IntervalSMTUtils.get_tracked_variable(domain, rvalue_name)
        if rvalue_var is not None:
            return True
        rvalue_var = self._materialize_missing_constant_version(rvalue_name, domain)
        return rvalue_var is not None

    def _check_sufficient_versions(
        self, rvalues: list[object], lvalue_name: str, domain: "IntervalDomain"
    ) -> bool:
        """Check if there are sufficient SSA versions for phi."""
        if len(rvalues) == 1:
            return True

        base_name = self._get_base_name(lvalue_name)
        if not base_name:
            return True

        version_count = self._count_concrete_versions(base_name, lvalue_name, domain)
        return version_count >= 2

    def _count_concrete_versions(
        self, base_name: str, lvalue_name: str, domain: "IntervalDomain"
    ) -> int:
        """Count concrete SSA versions (excluding input params)."""
        count = 0
        for var_name in domain.state.get_range_variables().keys():
            if var_name == lvalue_name:
                continue
            if var_name.startswith(base_name + "_"):
                if self._get_ssa_num(var_name) >= 2:
                    count += 1
        return count

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
        """Collect equality constraints for each rvalue in Phi operation."""
        lvalue_name = lvalue_var.base.name
        rvalue_names_from_ssa = self._collect_rvalue_names(rvalues)

        missing_versions = self._find_missing_phi_rvalues(
            lvalue_name, rvalue_names_from_ssa, domain
        )
        should_exclude_input = self._should_exclude_input_param(
            lvalue_name, rvalue_names_from_ssa, missing_versions, domain
        )

        rvalue_to_father: dict[str, "Node"] = {}
        if branch_info and node:
            rvalue_to_father = self._map_rvalues_to_fathers(rvalues, node)

        ctx = PhiContext(domain, branch_info, rvalue_to_father, should_exclude_input)
        or_constraints, used_names = self._constraints_from_rvalues(lvalue_var, rvalues, ctx)

        state = PhiConstraintsState(or_constraints, used_names)
        self._add_missing_version_constraints(lvalue_var, missing_versions, lvalue_name, state, ctx)

        return state.or_constraints

    def _collect_rvalue_names(self, rvalues: list[object]) -> set[str]:
        """Collect resolved names from rvalues."""
        names: set[str] = set()
        for rvalue in rvalues:
            name = IntervalSMTUtils.resolve_variable_name(rvalue)
            if name:
                names.add(name)
        return names

    def _constraints_from_rvalues(
        self,
        lvalue_var: "TrackedSMTVariable",
        rvalues: list[object],
        ctx: PhiContext,
    ) -> tuple[list[SMTTerm], set[str]]:
        """Collect constraints from explicit rvalues."""
        or_constraints: list[SMTTerm] = []
        used_names: set[str] = set()

        for rvalue in rvalues:
            rvalue_name = IntervalSMTUtils.resolve_variable_name(rvalue)
            if rvalue_name is None:
                continue

            if self._should_skip_rvalue(rvalue_name, ctx):
                continue

            rvalue_var = IntervalSMTUtils.get_tracked_variable(ctx.domain, rvalue_name)
            if rvalue_var is None:
                self.logger.debug(
                    "Rvalue '{rvalue_name}' not found in domain for Phi operation",
                    rvalue_name=rvalue_name,
                )
                continue

            constraint = self._create_equality_constraint(lvalue_var, rvalue_var)
            if constraint is not None:
                or_constraints.append(constraint)
                used_names.add(rvalue_name)

        return or_constraints, used_names

    def _should_skip_rvalue(self, rvalue_name: str, ctx: PhiContext) -> bool:
        """Determine if rvalue should be skipped."""
        if ctx.should_exclude_input and self._is_input_param_version(rvalue_name, ctx.domain):
            self.logger.debug(
                "Excluding input param '{rvalue_name}' from Phi (all branches assign)",
                rvalue_name=rvalue_name,
            )
            return True

        if self._is_unreachable_branch(rvalue_name, ctx.branch_info, ctx.rvalue_to_father):
            return True

        return False

    def _is_unreachable_branch(
        self,
        rvalue_name: str,
        branch_info: Optional[dict],
        rvalue_to_father: dict[str, "Node"],
    ) -> bool:
        """Check if rvalue is from an unreachable branch."""
        if not branch_info or branch_info.get('condition_value') is None:
            return False

        father = rvalue_to_father.get(rvalue_name)
        if father is None:
            return False

        condition_value = branch_info['condition_value']
        true_father = branch_info.get('true_branch_father')
        false_father = branch_info.get('false_branch_father')

        if condition_value is True and father == false_father:
            self.logger.debug(
                "Excluding '{rvalue_name}' from Phi (unreachable false branch)",
                rvalue_name=rvalue_name,
            )
            return True

        if condition_value is False and father == true_father:
            self.logger.debug(
                "Excluding '{rvalue_name}' from Phi (unreachable true branch)",
                rvalue_name=rvalue_name,
            )
            return True

        return False

    def _add_missing_version_constraints(
        self,
        lvalue_var: "TrackedSMTVariable",
        missing_versions: list[str],
        lvalue_name: str,
        state: PhiConstraintsState,
        ctx: PhiContext,
    ) -> None:
        """Add constraints for missing SSA versions."""
        for rvalue_name in missing_versions:
            if rvalue_name in state.used_names:
                continue
            rvalue_var = IntervalSMTUtils.get_tracked_variable(ctx.domain, rvalue_name)
            if rvalue_var is None:
                continue
            constraint = self._create_equality_constraint(lvalue_var, rvalue_var)
            if constraint is not None:
                state.or_constraints.append(constraint)
                self.logger.debug(
                    "Added missing SSA version '{rvalue_name}' to Phi for '{lvalue_name}'",
                    rvalue_name=rvalue_name,
                    lvalue_name=lvalue_name,
                )

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
        """Create a missing SSA version for constant/state vars by cloning an existing one."""
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
        parsed = self._parse_ssa_variable_name(lvalue_name)
        if parsed is None:
            return []
        base_name, lvalue_ssa_num = parsed

        missing: list[str] = []
        for var_name in domain.state.get_range_variables().keys():
            if self._is_missing_predecessor(
                var_name, lvalue_name, base_name, lvalue_ssa_num, used_rvalue_names
            ):
                missing.append(var_name)
        return missing

    def _parse_ssa_variable_name(self, lvalue_name: str) -> Optional[tuple[str, int]]:
        """Parse variable name to extract base name and SSA number.

        Format: "Contract.func().var|var_6" → ("Contract.func().var|var", 6)
        Returns None if the format doesn't match.
        """
        if "|" not in lvalue_name:
            return None

        parts = lvalue_name.rsplit("|", 1)
        prefix, ssa_part = parts[0], parts[1]

        if "_" not in ssa_part:
            return None

        base_var_name, ssa_num_str = ssa_part.rsplit("_", 1)
        try:
            ssa_num = int(ssa_num_str)
            return f"{prefix}|{base_var_name}", ssa_num
        except ValueError:
            return None

    def _is_missing_predecessor(
        self,
        var_name: str,
        lvalue_name: str,
        base_name: str,
        lvalue_ssa_num: int,
        used_rvalue_names: set[str],
    ) -> bool:
        """Check if var_name is a missing SSA predecessor for the phi."""
        if var_name in used_rvalue_names or var_name == lvalue_name:
            return False

        if not var_name.startswith(base_name + "_"):
            return False

        suffix = var_name[len(base_name) + 1:]
        try:
            ssa_num = int(suffix)
        except ValueError:
            return False

        if ssa_num >= lvalue_ssa_num:
            return False

        # Check if there's a used version with lower number (nested if-else case)
        return any(
            self._get_ssa_num(used) < ssa_num
            for used in used_rvalue_names
            if used.startswith(base_name + "_")
        )

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
        self, node: "Node", domain: "IntervalDomain"
    ) -> Optional[dict]:
        """Analyze if the branch leading to this phi has a known constant condition."""
        if self.solver is None:
            return None

        if_info = self._find_if_node_ancestor(node)
        if if_info is None:
            return None

        if_node, true_father, false_father = if_info

        condition_name = self._find_condition_name(if_node)
        if condition_name is None:
            return None

        condition_var = IntervalSMTUtils.get_tracked_variable(domain, condition_name)
        if condition_var is None:
            return None

        condition_value = self._get_explicit_constant_value(condition_var)

        return {
            'if_node': if_node,
            'condition_var': condition_name,
            'condition_value': condition_value,
            'true_branch_father': true_father,
            'false_branch_father': false_father,
        }

    def _find_if_node_ancestor(self, node: "Node") -> Optional[tuple]:
        """Find the IF node ancestor and branch fathers."""
        from slither.core.cfg.node import NodeType

        for father in node.fathers:
            for gfather in father.fathers:
                if gfather.type == NodeType.IF:
                    true_father, false_father = self._identify_branch_fathers(gfather, father)
                    return (gfather, true_father, false_father)
        return None

    def _identify_branch_fathers(
        self, if_node: "Node", current_father: "Node"
    ) -> tuple[Optional["Node"], Optional["Node"]]:
        """Identify which branch the current father came from."""
        true_father = None
        false_father = None
        if len(if_node.sons) == 2:
            if current_father == if_node.sons[0]:
                true_father = current_father
            elif current_father == if_node.sons[1]:
                false_father = current_father
        return true_father, false_father

    def _find_condition_name(self, if_node: "Node") -> Optional[str]:
        """Find the condition variable name from an IF node."""
        for ir in if_node.irs_ssa or []:
            if hasattr(ir, 'value'):
                return IntervalSMTUtils.resolve_variable_name(ir.value)
        return None

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

        member_names = self._find_struct_member_names(rvalues, domain)
        if not member_names:
            return

        for member_name in member_names:
            self._propagate_single_member(lvalue_name, member_name, rvalues, domain)

    def _find_struct_member_names(
        self, rvalues: list[object], domain: "IntervalDomain"
    ) -> set[str]:
        """Find all struct member names from rvalues."""
        member_names: set[str] = set()
        for rvalue in rvalues:
            rvalue_name = IntervalSMTUtils.resolve_variable_name(rvalue)
            if rvalue_name is None:
                continue
            rvalue_prefix = f"{rvalue_name}."
            for var_name in domain.state.get_variables_by_prefix(rvalue_prefix):
                member_name = var_name[len(rvalue_prefix):]
                member_names.add(member_name)
        return member_names

    def _propagate_single_member(
        self,
        lvalue_name: str,
        member_name: str,
        rvalues: list[object],
        domain: "IntervalDomain",
    ) -> None:
        """Propagate a single struct member through Phi."""
        lvalue_member_name = f"{lvalue_name}.{member_name}"
        lvalue_member_var = self._get_or_create_member_var(
            lvalue_member_name, member_name, rvalues, domain
        )
        if lvalue_member_var is None:
            return

        constraints = self._collect_member_constraints(
            lvalue_member_var, member_name, rvalues, domain
        )
        self._apply_or_constraints(constraints, lvalue_member_name)

    def _get_or_create_member_var(
        self,
        lvalue_member_name: str,
        member_name: str,
        rvalues: list[object],
        domain: "IntervalDomain",
    ) -> Optional[TrackedSMTVariable]:
        """Get or create the lvalue member variable."""
        var = IntervalSMTUtils.get_tracked_variable(domain, lvalue_member_name)
        if var is not None:
            return var

        member_type = self._infer_member_type(member_name, rvalues, domain)
        if member_type is None:
            return None

        var = IntervalSMTUtils.create_tracked_variable(
            self.solver, lvalue_member_name, member_type
        )
        if var is None:
            return None
        domain.state.set_range_variable(lvalue_member_name, var)
        var.assert_no_overflow(self.solver)
        return var

    def _infer_member_type(
        self, member_name: str, rvalues: list[object], domain: "IntervalDomain"
    ) -> Optional[ElementaryType]:
        """Infer member type from rvalue members."""
        for rvalue in rvalues:
            rvalue_name = IntervalSMTUtils.resolve_variable_name(rvalue)
            if rvalue_name is None:
                continue
            rvalue_member = IntervalSMTUtils.get_tracked_variable(
                domain, f"{rvalue_name}.{member_name}"
            )
            if rvalue_member is not None:
                type_str = rvalue_member.base.metadata.get("solidity_type")
                if type_str:
                    return ElementaryType(type_str)
        return None

    def _collect_member_constraints(
        self,
        lvalue_var: TrackedSMTVariable,
        member_name: str,
        rvalues: list[object],
        domain: "IntervalDomain",
    ) -> list[SMTTerm]:
        """Collect equality constraints for rvalue members."""
        constraints: list[SMTTerm] = []
        for rvalue in rvalues:
            rvalue_name = IntervalSMTUtils.resolve_variable_name(rvalue)
            if rvalue_name is None:
                continue
            rvalue_var = self._find_rvalue_member(rvalue_name, member_name, domain)
            if rvalue_var is None:
                continue
            constraint = self._create_equality_constraint(lvalue_var, rvalue_var)
            if constraint is not None:
                constraints.append(constraint)
        return constraints

    def _find_rvalue_member(
        self, rvalue_name: str, member_name: str, domain: "IntervalDomain"
    ) -> Optional[TrackedSMTVariable]:
        """Find rvalue member variable, trying alternate names."""
        var = IntervalSMTUtils.get_tracked_variable(domain, f"{rvalue_name}.{member_name}")
        if var is not None:
            return var
        # Try base name without SSA version
        rvalue_base = rvalue_name.split("|")[0] if "|" in rvalue_name else rvalue_name
        return IntervalSMTUtils.get_tracked_variable(domain, f"{rvalue_base}.{member_name}")

    def _apply_or_constraints(self, constraints: list[SMTTerm], member_name: str) -> None:
        """Apply OR constraints for struct member."""
        if not constraints:
            return
        if len(constraints) == 1:
            self.solver.assert_constraint(constraints[0])
        else:
            self.solver.assert_constraint(self.solver.Or(*constraints))
        self.logger.debug(
            "Propagated struct member '{member}' from {count} rvalue(s)",
            member=member_name,
            count=len(constraints),
        )
