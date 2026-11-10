"""Find source patterns affected by the legacy/via-IR semantic differences."""

from collections.abc import Iterator

from slither.core.cfg.node import Node, NodeType
from slither.core.declarations import Contract, Function, Modifier
from slither.core.declarations.function_contract import FunctionContract
from slither.core.expressions import (
    AssignmentOperation,
    CallExpression,
    Identifier,
    SuperCallExpression,
)
from slither.core.solidity_types import ElementaryType
from slither.core.variables.state_variable import StateVariable
from slither.core.variables.local_variable import LocalVariable
from slither.detectors.functions.modifier import is_revert
from slither.detectors.abstract_detector import (
    AbstractDetector,
    DETECTOR_INFO,
    DetectorClassification,
)
from slither.slithir.operations import InternalCall, LibraryCall
from slither.utils.output import Output


def call_target(operation: InternalCall | LibraryCall, context: Contract) -> Function | None:
    """Resolve virtual bare calls in inherited initializer expressions per deployment."""
    function = operation.function
    expression = operation.expression
    if (
        isinstance(operation, InternalCall)
        and isinstance(function, FunctionContract)
        and function.is_virtual
        and isinstance(expression, CallExpression)
        and not isinstance(expression, SuperCallExpression)
        and type(expression.called) is Identifier
    ):
        return context.get_function_from_full_name(function.full_name) or function
    return function


def called_functions(node: Node, context: Contract) -> Iterator[Function]:
    for operation in node.irs:
        if isinstance(operation, (InternalCall, LibraryCall)):
            function = call_target(operation, context)
            if function is not None:
                yield function


def reachable_functions(function: Function, context: Contract) -> Iterator[Function]:
    """Cycle-bounded traversal retaining explicit base/super call targets."""
    pending = [function]
    seen = set()
    while pending:
        current = pending.pop()
        if current in seen:
            continue
        seen.add(current)
        yield current
        pending.extend(current.modifiers)
        for node in current.nodes:
            pending.extend(called_functions(node, context))


def initializer_reads(node: Node, context: Contract) -> set[StateVariable]:
    reads = set(node.state_variables_read)
    for function in called_functions(node, context):
        for reachable in reachable_functions(function, context):
            reads.update(reachable.state_variables_read)
    return reads


def initializer_nodes(contract: Contract) -> dict[StateVariable, Node]:
    """Do not use the shared StateVariable.node_initialization of a sibling contract."""
    initializers = {}
    for function in contract.functions_declared:
        if not function.is_constructor_variables:
            continue
        for node in function.nodes:
            expression = node.expression
            if isinstance(expression, AssignmentOperation) and isinstance(
                expression.expression_left, Identifier
            ):
                variable = expression.expression_left.value
                if isinstance(variable, StateVariable):
                    initializers[variable] = node
    return initializers


def constructor_writes(constructor: Function, context: Contract) -> Iterator[StateVariable]:
    for function in reachable_functions(constructor, context):
        yield from function.state_variables_written


def repeats_body(modifier: Modifier) -> bool:
    """Two placeholders must be reachable on one CFG walk, including loops."""
    pending = [(modifier.entry_point, False)]
    seen = set()
    while pending:
        node, passed_placeholder = pending.pop()
        if node is None or (node, passed_placeholder) in seen:
            continue
        seen.add((node, passed_placeholder))
        if is_revert(node) or node.type is NodeType.RETURN:
            continue
        if node.type is NodeType.PLACEHOLDER:
            if passed_placeholder:
                return True
            passed_placeholder = True
        pending.extend((son, passed_placeholder) for son in node.sons)
    return False


def node_access(node: Node, variable: LocalVariable) -> tuple[bool, bool]:
    """Return whether the incoming value is read or overwritten first."""
    for operation in node.irs:
        if variable in operation.read:
            return True, False
        if getattr(operation, "lvalue", None) is variable:
            return False, True
    return False, False


def reads_before_assignment(function: Function, variable: LocalVariable) -> bool:
    """Whether the initial value can be read before a body assignment kills it."""
    pending = [function.entry_point]
    seen = set()
    while pending:
        node = pending.pop()
        if node is None or node in seen or is_revert(node):
            continue
        seen.add(node)
        # Modifier invocation nodes do not execute in the repeated function body.
        if any(isinstance(ir, InternalCall) and ir.is_modifier_call for ir in node.irs):
            pending.extend(node.sons)
            continue
        read, written = node_access(node, variable)
        implicit_return = (
            variable in function.returns and node.will_return and node.type is not NodeType.RETURN
        )
        if read or (implicit_return and not written):
            return True
        if not written:
            pending.extend(node.sons)
    return False


class IRConstructorOrder(AbstractDetector):
    LANGUAGE = "solidity"
    ARGUMENT = "ir-constructor-order"
    HELP = "State initializers depending on base-constructor writes change order with via-IR"
    IMPACT = DetectorClassification.LOW
    CONFIDENCE = DetectorClassification.MEDIUM
    WIKI = "https://docs.soliditylang.org/en/latest/ir-breaking-changes.html#semantic-only-changes"
    WIKI_TITLE = "Constructor initialization order changes with via-IR"
    WIKI_DESCRIPTION = """The legacy pipeline initializes state variables throughout the inheritance
hierarchy before executing constructors. The IR pipeline interleaves each contract's state
initializers with its constructor. An initializer that reads state written by a preceding base
constructor can therefore observe a different value. Internal helper calls are included. This is
an audit warning when planning a pipeline change, not proof of an exploitable vulnerability or a claim
that the current pipeline is incorrect. Value equality and path feasibility are not proved. External calls, assembly-only access and
dynamic internal calls are not modeled. The warning is emitted with either pipeline selected."""
    WIKI_EXPLOIT_SCENARIO = """A base constructor initializes an authorization threshold. A derived
state initializer copies that threshold. Enabling via-IR changes the copied value because the
base constructor now runs before the derived initializer."""
    WIKI_RECOMMENDATION = """Review the initializer and base constructor together. Make the intended
initialization order explicit and compare deployment behavior under both compiler pipelines."""

    @staticmethod
    def dependencies(
        contract: Contract,
    ) -> Iterator[tuple[StateVariable, Node, StateVariable, Function]]:
        preceding_writes: dict[StateVariable, Function] = {}
        initializers = initializer_nodes(contract)
        for base in [*reversed(contract.inheritance), contract]:
            for variable in base.state_variables_declared:
                node = initializers.get(variable)
                if node is None or variable.is_constant:
                    continue
                for read in sorted(
                    initializer_reads(node, contract), key=lambda item: item.canonical_name
                ):
                    if read in preceding_writes:
                        yield variable, node, read, preceding_writes[read]
            constructor = base.constructors_declared
            if constructor:
                preceding_writes.update(
                    dict.fromkeys(constructor_writes(constructor, contract), constructor)
                )

    def _detect(self) -> list[Output]:
        results = []
        # A concrete contract stays deployable when it has descendants, so derived
        # leaves alone are not every deployment context. Scan those contracts too,
        # reporting each distinct finding once under the first context that shows it.
        contexts = list(self.compilation_unit.contracts_derived)
        contexts.extend(
            contract
            for contract in self.compilation_unit.contracts
            if contract not in contexts and not contract.is_abstract
        )
        seen: set[tuple[str, str, int, int, str, str]] = set()
        for contract in contexts:
            for variable, node, read, constructor in self.dependencies(contract):
                # Each context gets its own initializer nodes, so identity comes
                # from the source location, not the node objects.
                mapping = node.source_mapping
                key = (
                    variable.canonical_name,
                    mapping.filename.absolute,
                    mapping.start,
                    mapping.length,
                    read.canonical_name,
                    constructor.canonical_name,
                )
                if key in seen:
                    continue
                seen.add(key)
                info: DETECTOR_INFO = [
                    variable,
                    " in ",
                    contract,
                    " reads ",
                    read,
                    " before ",
                    constructor,
                    " in legacy codegen, but after it with via-IR:\n\t- ",
                    node,
                    "\n",
                ]
                results.append(self.generate_result(info))
        return results


class IRRepeatedModifier(AbstractDetector):
    LANGUAGE = "solidity"
    ARGUMENT = "ir-repeated-modifier"
    HELP = "Repeated modifier bodies can observe reset parameters/returns with via-IR"
    IMPACT = DetectorClassification.LOW
    CONFIDENCE = DetectorClassification.MEDIUM
    WIKI = "https://docs.soliditylang.org/en/latest/ir-breaking-changes.html#semantic-only-changes"
    WIKI_TITLE = "Repeated modifier body semantics change with via-IR"
    WIKI_DESCRIPTION = """When a modifier executes the function body repeatedly, the legacy pipeline
shares function parameter and return-variable stack slots between executions. The IR pipeline
passes the original parameters anew and resets return variables. This detector finds a reachable
repeated placeholder and an elementary parameter/return variable whose initial value can be read
and whose value is written in the body. Mutually exclusive placeholders alone are not repeated.
This is a migration audit warning: it does not prove path feasibility or unequal final values,
and does not cover reference-type aliases, assembly-only writes or dynamic internal calls.
It checks each directly applied modifier separately and does not model modifiers applied to
modifiers. The warning is emitted with either pipeline selected."""
    WIKI_EXPLOIT_SCENARIO = """A modifier executes `_` twice. A function increments a named return
variable on each execution and returns 2 with legacy codegen but 1 with via-IR. A caller relying
on the accumulated result changes behavior when the compilation pipeline changes."""
    WIKI_RECOMMENDATION = """Execute the function body once, or make accumulation explicit in a
separate helper with explicit inputs and outputs. Test both pipelines before migrating."""

    @staticmethod
    def affected(function: Function) -> list[LocalVariable]:
        written = set(function.variables_written)
        return [
            variable
            for variable in [*function.parameters, *function.returns]
            if isinstance(variable.type, ElementaryType)
            and variable in written
            and reads_before_assignment(function, variable)
        ]

    def _result(
        self, function: Function, modifier: Modifier, variables: list[LocalVariable]
    ) -> Output:
        info: DETECTOR_INFO = [
            function,
            " reads and writes parameters/return variables across repeated body executions by ",
            modifier,
            "; via-IR resets their initial values on each execution:\n",
        ]
        for variable in variables:
            info.extend(["\t- ", variable, "\n"])
        return self.generate_result(info)

    def _detect(self) -> list[Output]:
        results = []
        repeated = {
            modifier
            for contract in self.compilation_unit.contracts
            for modifier in contract.modifiers
            if repeats_body(modifier)
        }
        for contract in self.compilation_unit.contracts_derived:
            for function in contract.functions:
                if function.is_constructor or function.is_constructor_variables:
                    continue
                variables = self.affected(function)
                if not variables:
                    continue
                for modifier in function.modifiers:
                    if modifier in repeated:
                        results.append(self._result(function, modifier, variables))
        return results
