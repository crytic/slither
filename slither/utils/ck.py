"""
    CK Metrics are a suite of six software metrics proposed by Chidamber and Kemerer in 1994.
    These metrics are used to measure the complexity of a class.
    https://en.wikipedia.org/wiki/Programming_complexity

    - Response For a Class (RFC) is a metric that measures the number of unique method calls within a class.
    - Number of Children (NOC) is a metric that measures the number of children a class has.
    - Depth of Inheritance Tree (DIT) is a metric that measures the number of parent classes a class has.
    - Coupling Between Object Classes (CBO) is a metric that measures the number of classes a class is coupled to.

    Not implemented:
    - Lack of Cohesion of Methods (LCOM) is a metric that measures the lack of cohesion in methods.
    - Weighted Methods per Class (WMC) is a metric that measures the complexity of a class.

    During the calculation of the metrics above, there are a number of other intermediate metrics that are calculated.
    These are also included in the output:
     - State variables: total number of state variables
     - Constants: total number of constants
     - Immutables: total number of immutables
     - Public: total number of public functions
     - External: total number of external functions
     - Internal: total number of internal functions
     - Private: total number of private functions
     - Mutating: total number of state mutating functions
     - View: total number of view functions
     - Pure: total number of pure functions
     - External mutating: total number of external mutating functions
     - No auth or onlyOwner: total number of functions without auth or onlyOwner modifiers
     - No modifiers: total number of functions without modifiers
     - Ext calls: total number of external calls

"""
from collections import OrderedDict
from typing import Tuple, List, Dict
from dataclasses import dataclass, field
from slither.utils.colors import bold
from slither.core.declarations import Contract
from slither.utils.myprettytable import make_pretty_table, MyPrettyTable
from slither.utils.martin import MartinMetrics
from slither.slithir.operations.high_level_call import HighLevelCall


# Utility functions


def compute_dit(contract: Contract, depth: int = 0) -> int:
    """
    Recursively compute the depth of inheritance tree (DIT) of a contract
    Args:
        contract(core.declarations.contract.Contract): contract to compute DIT for
        depth(int): current depth of the contract
    Returns:
        int: depth of the contract
    """
    if not contract.inheritance:
        return depth
    max_dit = depth
    for inherited_contract in contract.inheritance:
        dit = compute_dit(inherited_contract, depth + 1)
        max_dit = max(max_dit, dit)
    return max_dit


def has_auth(func) -> bool:
    """
    Check if a function has no auth or only_owner modifiers
    Args:
        func(core.declarations.function.Function): function to check
    Returns:
        bool True if it does have auth or only_owner modifiers
    """
    for modifier in func.modifiers:
        if "auth" in modifier.name or "only_owner" in modifier.name:
            return True
    return False


# Utility classes for calculating CK metrics


@dataclass
# pylint: disable=too-many-instance-attributes
class CKContractMetrics:
    """Class to hold the CK metrics for a single contract."""

    contract: Contract

    # Used to calculate CBO - should be passed in as a constructor arg
    martin_metrics: Dict

    # Used to calculate NOC
    dependents: Dict

    state_variables: int = 0
    constants: int = 0
    immutables: int = 0
    public: int = 0
    external: int = 0
    internal: int = 0
    private: int = 0
    mutating: int = 0
    view: int = 0
    pure: int = 0
    external_mutating: int = 0
    no_auth_or_only_owner: int = 0
    no_modifiers: int = 0
    ext_calls: int = 0
    rfc: int = 0
    noc: int = 0
    dit: int = 0
    cbo: int = 0

    def __post_init__(self) -> None:
        if not hasattr(self.contract, "functions"):
            return
        self.count_variables()
        self.noc = len(self.dependents[self.contract.name])
        self.dit = compute_dit(self.contract)
        self.cbo = (
            self.martin_metrics[self.contract.name].ca + self.martin_metrics[self.contract.name].ce
        )
        self.calculate_metrics()

    # pylint: disable=too-many-locals
    # pylint: disable=too-many-branches
    def calculate_metrics(self) -> None:
        """Calculate the metrics for a contract"""
        rfc = self.public  # initialize with public getter count
        for func in self.contract.functions:
            if func.name == "constructor":
                continue
            pure = func.pure
            view = not pure and func.view
            mutating = not pure and not view
            external = func.visibility == "external"
            public = func.visibility == "public"
            internal = func.visibility == "internal"
            private = func.visibility == "private"
            external_public_mutating = external or public and mutating
            external_no_auth = external_public_mutating and not has_auth(func)
            external_no_modifiers = external_public_mutating and len(func.modifiers) == 0
            if external or public:
                rfc += 1

            high_level_calls = [
                ir for node in func.nodes for ir in node.irs_ssa if isinstance(ir, HighLevelCall)
            ]

            # convert irs to string with target function and contract name
            external_calls = []
            for high_level_call in high_level_calls:
                if isinstance(high_level_call.destination, Contract):
                    destination_contract = high_level_call.destination.name
                elif isinstance(high_level_call.destination, str):
                    destination_contract = high_level_call.destination
                elif not hasattr(high_level_call.destination, "type"):
                    continue
                elif isinstance(high_level_call.destination.type, Contract):
                    destination_contract = high_level_call.destination.type.name
                elif isinstance(high_level_call.destination.type, str):
                    destination_contract = high_level_call.destination.type
                elif not hasattr(high_level_call.destination.type, "type"):
                    continue
                elif isinstance(high_level_call.destination.type.type, Contract):
                    destination_contract = high_level_call.destination.type.type.name
                elif isinstance(high_level_call.destination.type.type, str):
                    destination_contract = high_level_call.destination.type.type
                else:
                    continue
                external_calls.append(f"{high_level_call.function_name}{destination_contract}")
            rfc += len(set(external_calls))

            self.public += public
            self.external += external
            self.internal += internal
            self.private += private

            self.mutating += mutating
            self.view += view
            self.pure += pure

            self.external_mutating += external_public_mutating
            self.no_auth_or_only_owner += external_no_auth
            self.no_modifiers += external_no_modifiers

            self.ext_calls += len(external_calls)
            self.rfc = rfc

    def count_variables(self) -> None:
        """Count the number of variables in a contract"""
        state_variable_count = 0
        constant_count = 0
        immutable_count = 0
        public_getter_count = 0
        for variable in self.contract.variables:
            if variable.is_constant:
                constant_count += 1
            elif variable.is_immutable:
                immutable_count += 1
            else:
                state_variable_count += 1
            if variable.visibility == "Public":
                public_getter_count += 1
        self.state_variables = state_variable_count
        self.constants = constant_count
        self.immutables = immutable_count

        # initialize RFC with public getter count
        # self.public is used count public functions not public variables
        self.rfc = public_getter_count

    def to_dict(self) -> Dict[str, float]:
        """Return the metrics as a dictionary."""
        return OrderedDict(
            {
                "State variables": self.state_variables,
                "Constants": self.constants,
                "Immutables": self.immutables,
                "Public": self.public,
                "External": self.external,
                "Internal": self.internal,
                "Private": self.private,
                "Mutating": self.mutating,
                "View": self.view,
                "Pure": self.pure,
                "External mutating": self.external_mutating,
                "No auth or onlyOwner": self.no_auth_or_only_owner,
                "No modifiers": self.no_modifiers,
                "Ext calls": self.ext_calls,
                "RFC": self.rfc,
                "NOC": self.noc,
                "DIT": self.dit,
                "CBO": self.cbo,
            }
        )


@dataclass
class SectionInfo:
    """Class to hold the information for a section of the report."""

    title: str
    pretty_table: MyPrettyTable
    txt: str


@dataclass
# pylint: disable=too-many-instance-attributes
class CKMetrics:
    """Class to hold the CK metrics for all contracts. Contains methods useful for reporting.

    There are 5 sections in the report:
    1. Variable count by type (state, constant, immutable)
    2. Function count by visibility (public, external, internal, private)
    3. Function count by mutability (mutating, view, pure)
    4. External mutating function count by modifier (external mutating, no auth or onlyOwner, no modifiers)
    5. CK metrics (RFC, NOC, DIT, CBO)
    """

    contracts: List[Contract] = field(default_factory=list)
    contract_metrics: OrderedDict = field(default_factory=OrderedDict)
    title: str = "CK complexity metrics"
    full_text: str = ""
    auxiliary1: SectionInfo = field(default=SectionInfo)
    auxiliary2: SectionInfo = field(default=SectionInfo)
    auxiliary3: SectionInfo = field(default=SectionInfo)
    auxiliary4: SectionInfo = field(default=SectionInfo)
    core: SectionInfo = field(default=SectionInfo)
    AUXILIARY1_KEYS = (
        "State variables",
        "Constants",
        "Immutables",
    )
    AUXILIARY2_KEYS = (
        "Public",
        "External",
        "Internal",
        "Private",
    )
    AUXILIARY3_KEYS = (
        "Mutating",
        "View",
        "Pure",
    )
    AUXILIARY4_KEYS = (
        "External mutating",
        "No auth or onlyOwner",
        "No modifiers",
    )
    CORE_KEYS = (
        "Ext calls",
        "RFC",
        "NOC",
        "DIT",
        "CBO",
    )
    SECTIONS: Tuple[Tuple[str, str, Tuple[str]]] = (
        ("Variables", "auxiliary1", AUXILIARY1_KEYS),
        ("Function visibility", "auxiliary2", AUXILIARY2_KEYS),
        ("State mutability", "auxiliary3", AUXILIARY3_KEYS),
        ("External mutating functions", "auxiliary4", AUXILIARY4_KEYS),
        ("Core", "core", CORE_KEYS),
    )

    def __post_init__(self) -> None:
        martin_metrics = MartinMetrics(self.contracts).contract_metrics
        dependents = {
            inherited.name: {
                contract.name
                for contract in self.contracts
                if inherited.name in contract.inheritance
            }
            for inherited in self.contracts
        }
        for contract in self.contracts:
            self.contract_metrics[contract.name] = CKContractMetrics(
                contract=contract, martin_metrics=martin_metrics, dependents=dependents
            )

        # Create the table and text for each section.
        data = {
            contract.name: self.contract_metrics[contract.name].to_dict()
            for contract in self.contracts
        }

        subtitle = ""
        # Update each section
        for (title, attr, keys) in self.SECTIONS:
            if attr == "core":
                # Special handling for core section
                totals_enabled = False
                subtitle += bold("RFC: Response For a Class\n")
                subtitle += bold("NOC: Number of Children\n")
                subtitle += bold("DIT: Depth of Inheritance Tree\n")
                subtitle += bold("CBO: Coupling Between Object Classes\n")
            else:
                totals_enabled = True
                subtitle = ""

            pretty_table = make_pretty_table(["Contract", *keys], data, totals=totals_enabled)
            section_title = f"{self.title} ({title})"
            txt = f"\n\n{section_title}:\n{subtitle}{pretty_table}\n"
            self.full_text += txt
            setattr(
                self,
                attr,
                SectionInfo(title=section_title, pretty_table=pretty_table, txt=txt),
            )
