from slither.analyses.data_dependency.data_dependency import is_dependent
from slither.core.cfg.node import Node, NodeType
from slither.core.compilation_unit import SlitherCompilationUnit
from slither.core.declarations import Contract, Function, SolidityVariableComposed, FunctionContract
from slither.core.declarations.solidity_variables import SolidityVariable
from slither.core.solidity_types import ElementaryType
from slither.core.variables.local_variable import LocalVariable
from slither.slithir.operations import (
    Assignment,
    Binary,
    BinaryType,
    Condition,
    HighLevelCall,
    InternalCall,
    LibraryCall,
    Member,
    OperationWithLValue,
    SolidityCall,
    TypeConversion,
    Unary,
    UnaryType,
)
from slither.slithir.variables import Constant


class ArbitrarySendErc20:
    """Detects instances where ERC20 can be sent from an arbitrary from address."""

    def __init__(self, compilation_unit: SlitherCompilationUnit) -> None:
        self._compilation_unit = compilation_unit
        self._no_permit_results: list[Node] = []
        self._permit_results: list[Node] = []

    @property
    def compilation_unit(self) -> SlitherCompilationUnit:
        return self._compilation_unit

    @property
    def no_permit_results(self) -> list[Node]:
        return self._no_permit_results

    @property
    def permit_results(self) -> list[Node]:
        return self._permit_results

    def _detect_arbitrary_from(self, contract: Contract) -> None:
        for f in contract.functions:
            all_high_level_calls = [
                ir.function.solidity_signature
                for _, ir in f.high_level_calls
                if isinstance(ir.function, Function)
            ]
            all_library_calls = [ir.function.solidity_signature for ir in f.library_calls]
            if (
                "transferFrom(address,address,uint256)" in all_high_level_calls
                or "safeTransferFrom(address,address,address,uint256)" in all_library_calls
            ):
                if (
                    "permit(address,address,uint256,uint256,uint8,bytes32,bytes32)"
                    in all_high_level_calls
                ):
                    ArbitrarySendErc20._arbitrary_from(f, self._permit_results)
                else:
                    ArbitrarySendErc20._arbitrary_from(f, self._no_permit_results)

    @staticmethod
    def _arbitrary_from(function: FunctionContract, results: list[Node]) -> None:
        """Finds instances of (safe)transferFrom that do not use msg.sender or address(this) as from parameter.

        A `from` whose signature is verified on every path to the transfer is not reported.
        """
        for _, ir in function.high_level_calls:
            if (
                isinstance(ir, LibraryCall)
                and ir.function.solidity_signature
                == "safeTransferFrom(address,address,address,uint256)"
                and not (
                    is_dependent(
                        ir.arguments[1],
                        SolidityVariableComposed("msg.sender"),
                        ir.node,
                    )
                    or is_dependent(
                        ir.arguments[1],
                        SolidityVariable("this"),
                        ir.node,
                    )
                    or _is_signature_authorized(ir.node, ir.arguments[1])
                )
            ):
                results.append(ir.node)
            elif (
                isinstance(ir, HighLevelCall)
                and isinstance(ir.function, Function)
                and ir.function.solidity_signature == "transferFrom(address,address,uint256)"
                and not (
                    is_dependent(
                        ir.arguments[0],
                        SolidityVariableComposed("msg.sender"),
                        ir.node,
                    )
                    or is_dependent(
                        ir.arguments[0],
                        SolidityVariable("this"),
                        ir.node,
                    )
                    or _is_signature_authorized(ir.node, ir.arguments[0])
                )
            ):
                results.append(ir.node)

    def detect(self) -> None:
        """Detect transfers that use arbitrary `from` parameter."""
        for c in self.compilation_unit.contracts_derived:
            self._detect_arbitrary_from(c)


_MAX_CALLEE_DEPTH = 3
_ERC1271_MAGIC_VALUE = 0x1626BA7E

# Names a value as a parameter index followed by the struct members read from it.
Key = tuple[int | str, ...]
# (signer, digest): a signature of `signer` over `digest` is verified. A digest read from a
# parameter is keyed like any other value. Every other digest is None and is only recorded when it
# is computed from the signer itself or from the whole parameter that holds the signer.
Fact = tuple[Key, Key | None]


def _is_signature_authorized(node: Node, from_value: object) -> bool:
    """True when a signature of `from_value` over a digest computed from it is verified on every
    path that reaches `node`."""
    facts = _SignatureFacts(node.function, _MAX_CALLEE_DEPTH)
    from_key = facts.key(from_value)
    return from_key is not None and any(
        signer == from_key and digest is None for signer, digest in facts.before(node)
    )


def _callee_name(ir: object) -> str:
    return getattr(getattr(ir, "function", None), "name", "") or ""


def _is_signature_check(ir: object) -> bool:
    """OpenZeppelin SignatureChecker and Solady SignatureCheckerLib: isValid*SignatureNow*(signer, hash, ...)."""
    name = _callee_name(ir)
    return (
        isinstance(ir, (LibraryCall, InternalCall))
        and name.startswith("isValid")
        and "SignatureNow" in name
        and len(ir.arguments) >= 2
    )


def _is_recovery(ir: object) -> bool:
    """ecrecover and the OpenZeppelin / Solady ECDSA.recover(digest, ...) entry points."""
    name = _callee_name(ir)
    if isinstance(ir, SolidityCall):
        return name.startswith("ecrecover(")
    return isinstance(ir, (LibraryCall, InternalCall)) and name in ("recover", "recoverCalldata")


def _always_reverts(node: Node) -> bool:
    return node.type is NodeType.THROW or any(
        isinstance(ir, SolidityCall) and ir.function.name.startswith("revert") for ir in node.irs
    )


def _reaches(start: Node | None, target: Node) -> bool:
    """Reachability in the CFG where a reverting node has no successors."""
    pending = [] if start is None else [start]
    seen: set[Node] = set()
    while pending:
        node = pending.pop()
        if node is target:
            return True
        if node not in seen:
            seen.add(node)
            if not _always_reverts(node):
                pending.extend(node.sons)
    return False


class _SignatureFacts:
    """Signature checks that must have succeeded when execution reaches a node of `function`.

    Checks are looked for in `function` and, down to `depth` levels, in the internal functions it
    calls. Facts are keyed on the parameters of `function`, so the facts of a callee are rewritten
    in terms of the arguments of the call.
    """

    def __init__(
        self,
        function: Function,
        depth: int,
        on_return_cache: dict[tuple[int, int], set[Fact]] | None = None,
    ) -> None:
        self._function = function
        self._depth = depth
        self._on_return_cache = {} if on_return_cache is None else on_return_cache
        self._definitions: dict[int, list[OperationWithLValue]] = {}
        for node in function.nodes:
            for ir in node.irs:
                if isinstance(ir, OperationWithLValue) and ir.lvalue is not None:
                    self._definitions.setdefault(id(ir.lvalue), []).append(ir)

    def _single_definition(self, variable: object) -> object:
        """The only operation that assigns `variable`. A local that is assigned outside its
        declaration may still hold its default value, so it has no single definition."""
        definitions = self._definitions.get(id(variable), [])
        if len(definitions) != 1:
            return None
        definition = definitions[0]
        if (
            isinstance(definition, Assignment)
            and isinstance(definition.lvalue, LocalVariable)
            and definition.node.type is not NodeType.VARIABLE
        ):
            return None
        return definition

    def key(self, variable: object) -> Key | None:
        """Names `variable` as a parameter that is never written, followed by member reads.
        Anything else, such as a storage read or a value that is assigned twice, has no key."""
        for index, parameter in enumerate(self._function.parameters):
            if variable is parameter:
                written = any(variable is w for w in self._function.variables_written)
                return None if written else (index,)
        definition = self._single_definition(variable)
        if isinstance(definition, Member):
            base = self.key(definition.variable_left)
            return None if base is None else (*base, definition.variable_right.value)
        if isinstance(definition, TypeConversion):
            return self.key(definition.variable)
        if isinstance(definition, Assignment) and isinstance(
            getattr(variable, "type", None), ElementaryType
        ):
            return self.key(definition.rvalue)
        return None

    def before(self, node: Node) -> set[Fact]:
        """Facts that hold whenever `node` is reached."""
        facts: set[Fact] = set()
        for guard in node.dominators:
            if guard is not node:
                facts |= self._guard_facts(guard, node) | self._callee_facts(guard)
        return facts

    def on_return(self) -> set[Fact]:
        """Facts that hold whenever the function returns normally."""
        cache_key = (id(self._function), self._depth)
        if cache_key not in self._on_return_cache:
            exits = [n for n in self._function.nodes if not n.sons and not _always_reverts(n)]
            per_exit = [
                self.before(n) | self._guard_facts(n, n) | self._callee_facts(n) for n in exits
            ]
            self._on_return_cache[cache_key] = set.intersection(*per_exit) if per_exit else set()
        return self._on_return_cache[cache_key]

    def _guard_facts(self, guard: Node, target: Node) -> set[Fact]:
        """Facts implied by a require/assert in `guard`, or by an `if` that only one of its
        branches lets the execution leave towards `target`."""
        if guard.type in (NodeType.IF, NodeType.IFLOOP):
            taken = _reaches(guard.son_true, target)
            if taken == _reaches(guard.son_false, target):
                return set()
            conditions = [(ir.value, taken) for ir in guard.irs if isinstance(ir, Condition)]
        else:
            conditions = [
                (ir.arguments[0], True)
                for ir in guard.irs
                if isinstance(ir, SolidityCall)
                and ir.function.name.startswith(("require(", "assert("))
            ]
        facts: set[Fact] = set()
        for value, truth in conditions:
            facts |= self._implied(value, truth)
        return facts

    def _implied(self, value: object, truth: bool) -> set[Fact]:
        """Facts that hold when the boolean `value` evaluates to `truth`."""
        ir = self._single_definition(value)
        if isinstance(ir, Unary) and ir.type is UnaryType.BANG:
            return self._implied(ir.rvalue, not truth)
        if isinstance(ir, Assignment):
            return self._implied(ir.rvalue, truth)
        if isinstance(ir, Binary):
            if (ir.type is BinaryType.ANDAND and truth) or (
                ir.type is BinaryType.OROR and not truth
            ):
                return self._implied(ir.variable_left, truth) | self._implied(
                    ir.variable_right, truth
                )
            if ir.type in (BinaryType.EQUAL, BinaryType.NOT_EQUAL):
                if truth == (ir.type is BinaryType.EQUAL):
                    return self._equality_facts(ir.variable_left, ir.variable_right)
            return set()
        if truth and _is_signature_check(ir):
            return self._fact(ir.arguments[0], ir.arguments[1])
        return set()

    def _equality_facts(self, left: object, right: object) -> set[Fact]:
        facts: set[Fact] = set()
        for result, other in ((left, right), (right, left)):
            call = self._recovery(result)
            if call is not None:
                facts |= self._fact(other, call.arguments[0])
            call = self._single_definition(result)
            if (
                isinstance(call, HighLevelCall)
                and not isinstance(call, LibraryCall)
                and _callee_name(call) == "isValidSignature"
                and len(call.arguments) == 2
                and self._is_erc1271_magic_value(other)
            ):
                facts |= self._fact(call.destination, call.arguments[0])
        return facts

    def _recovery(self, value: object) -> object:
        """The ecrecover / ECDSA.recover call that produced `value`, if any."""
        definition = self._single_definition(value)
        if isinstance(definition, Assignment):
            return self._recovery(definition.rvalue)
        if isinstance(definition, TypeConversion):
            return self._recovery(definition.variable)
        return definition if _is_recovery(definition) else None

    def _is_erc1271_magic_value(self, value: object) -> bool:
        """`value` is the constant IERC1271.isValidSignature.selector, however it is spelled."""
        if isinstance(value, Constant):
            return str(value.value) == str(_ERC1271_MAGIC_VALUE)
        definition = self._single_definition(value)
        if isinstance(definition, Assignment):
            return self._is_erc1271_magic_value(definition.rvalue)
        if isinstance(definition, TypeConversion):
            return self._is_erc1271_magic_value(definition.variable)
        return False

    def _fact(self, signer: object, digest: object) -> set[Fact]:
        signer_key = self.key(signer)
        if signer_key is None:
            return set()
        digest_key = self.key(digest)
        if digest_key is None and not self._reads_signer(digest, signer_key, {}):
            return set()
        return {(signer_key, digest_key)}

    def _reads_signer(self, value: object, signer: Key, memo: dict[int, bool]) -> bool:
        """True when every assignment of `value` is computed, through operands, from the signer or
        from the whole parameter that holds it. Another member of that parameter does not count,
        as it can be chosen independently of the signer. A value in the middle of its own
        computation counts as not reading it."""
        for position, parameter in enumerate(self._function.parameters):
            if value is parameter:
                return position == signer[0]
        member = self.key(value)
        if member is not None:
            own = signer[1:]
            return member[0] == signer[0] and member[1:][: len(own)] == own[: len(member) - 1]
        if id(value) not in memo:
            memo[id(value)] = False
            definitions = self._definitions.get(id(value), [])
            memo[id(value)] = bool(definitions) and all(
                any(self._reads_signer(operand, signer, memo) for operand in definition.read)
                for definition in definitions
            )
        return memo[id(value)]

    def _callee_facts(self, node: Node) -> set[Fact]:
        """Facts established by internal calls of `node`. A node that short-circuits may skip
        the call, so its calls are not trusted."""
        if self._depth == 0 or any(
            isinstance(ir, Binary) and ir.type in (BinaryType.ANDAND, BinaryType.OROR)
            for ir in node.irs
        ):
            return set()
        facts: set[Fact] = set()
        for ir in node.irs:
            if not (isinstance(ir, InternalCall) and isinstance(ir.function, Function)):
                continue
            callee = _SignatureFacts(ir.function, self._depth - 1, self._on_return_cache)
            for signer, digest in callee.on_return():
                signer_key = self._rebase(signer, ir.arguments)
                if signer_key is None:
                    continue
                digest_key = None if digest is None else self._rebase(digest, ir.arguments)
                if digest_key is None and digest is not None:
                    computed = ir.arguments[digest[0]] if digest[0] < len(ir.arguments) else None
                    if not self._reads_signer(computed, signer_key, {}):
                        continue
                facts.add((signer_key, digest_key))
        return facts

    def _rebase(self, key: Key, arguments: list) -> Key | None:
        """Rewrites a key on the parameters of a callee in terms of the caller."""
        if key[0] >= len(arguments):
            return None
        base = self.key(arguments[key[0]])
        return None if base is None else (*base, *key[1:])
