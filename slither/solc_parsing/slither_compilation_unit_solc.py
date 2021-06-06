import json
import logging
import os
import re
from typing import List, Dict

from slither.analyses.data_dependency.data_dependency import compute_dependency
from slither.core.compilation_unit import SlitherCompilationUnit
from slither.core.declarations import Contract
from slither.core.declarations.enum_top_level import EnumTopLevel
from slither.core.declarations.function_top_level import FunctionTopLevel
from slither.core.declarations.import_directive import Import
from slither.core.declarations.pragma_directive import Pragma
from slither.core.declarations.structure_top_level import StructureTopLevel
from slither.core.variables.top_level_variable import TopLevelVariable
from slither.exceptions import SlitherException
from slither.solc_parsing.declarations.contract import ContractSolc
from slither.solc_parsing.declarations.function import FunctionSolc
from slither.solc_parsing.declarations.structure_top_level import StructureTopLevelSolc
from slither.solc_parsing.exceptions import VariableNotFound
from slither.solc_parsing.variables.top_level_variable import TopLevelVariableSolc

logging.basicConfig()
logger = logging.getLogger("SlitherSolcParsing")
logger.setLevel(logging.INFO)


class SlitherCompilationUnitSolc:
    # pylint: disable=no-self-use,too-many-instance-attributes
    def __init__(self, compilation_unit: SlitherCompilationUnit):
        super().__init__()

        self._contracts_by_id: Dict[int, ContractSolc] = {}
        self._parsed = False
        self._analyzed = False

        self._underlying_contract_to_parser: Dict[Contract, ContractSolc] = dict()
        self._structures_top_level_parser: List[StructureTopLevelSolc] = []
        self._variables_top_level_parser: List[TopLevelVariableSolc] = []
        self._functions_top_level_parser: List[FunctionSolc] = []

        self._is_compact_ast = False
        # self._core: SlitherCore = core
        self._compilation_unit = compilation_unit

        self._all_functions_and_modifier_parser: List[FunctionSolc] = []

        self._top_level_contracts_counter = 0

    @property
    def compilation_unit(self) -> SlitherCompilationUnit:
        return self._compilation_unit

    @property
    def all_functions_and_modifiers_parser(self) -> List[FunctionSolc]:
        return self._all_functions_and_modifier_parser

    def add_function_or_modifier_parser(self, f: FunctionSolc):
        self._all_functions_and_modifier_parser.append(f)

    @property
    def underlying_contract_to_parser(self) -> Dict[Contract, ContractSolc]:
        return self._underlying_contract_to_parser

    ###################################################################################
    ###################################################################################
    # region AST
    ###################################################################################
    ###################################################################################

    def get_key(self) -> str:
        if self._is_compact_ast:
            return "nodeType"
        return "name"

    def get_children(self) -> str:
        if self._is_compact_ast:
            return "nodes"
        return "children"

    @property
    def is_compact_ast(self) -> bool:
        return self._is_compact_ast

    # endregion
    ###################################################################################
    ###################################################################################
    # region Parsing
    ###################################################################################
    ###################################################################################

    def parse_top_level_from_json(self, json_data: str) -> bool:
        try:
            data_loaded = json.loads(json_data)
            # Truffle AST
            if "ast" in data_loaded:
                self.parse_top_level_from_loaded_json(data_loaded["ast"], data_loaded["sourcePath"])
                return True
            # solc AST, where the non-json text was removed
            if "attributes" in data_loaded:
                filename = data_loaded["attributes"]["absolutePath"]
            else:
                filename = data_loaded["absolutePath"]
            self.parse_top_level_from_loaded_json(data_loaded, filename)
            return True
        except ValueError:

            first = json_data.find("{")
            if first != -1:
                last = json_data.rfind("}") + 1
                filename = json_data[0:first]
                json_data = json_data[first:last]

                data_loaded = json.loads(json_data)
                self.parse_top_level_from_loaded_json(data_loaded, filename)
                return True
            return False

    def _parse_enum(self, top_level_data: Dict):
        if self.is_compact_ast:
            name = top_level_data["name"]
            canonicalName = top_level_data["canonicalName"]
        else:
            name = top_level_data["attributes"][self.get_key()]
            if "canonicalName" in top_level_data["attributes"]:
                canonicalName = top_level_data["attributes"]["canonicalName"]
            else:
                canonicalName = name
        values = []
        children = (
            top_level_data["members"]
            if "members" in top_level_data
            else top_level_data.get("children", [])
        )
        for child in children:
            assert child[self.get_key()] == "EnumValue"
            if self.is_compact_ast:
                values.append(child["name"])
            else:
                values.append(child["attributes"][self.get_key()])

        enum = EnumTopLevel(name, canonicalName, values)
        enum.set_offset(top_level_data["src"], self._compilation_unit)
        self._compilation_unit.enums_top_level.append(enum)

    def parse_top_level_from_loaded_json(
        self, data_loaded: Dict, filename: str
    ):  # pylint: disable=too-many-branches,too-many-statements
        if "nodeType" in data_loaded:
            self._is_compact_ast = True

        if "sourcePaths" in data_loaded:
            for sourcePath in data_loaded["sourcePaths"]:
                if os.path.isfile(sourcePath):
                    self._compilation_unit.core.add_source_code(sourcePath)

        if data_loaded[self.get_key()] == "root":
            logger.error("solc <0.4 is not supported")
            return
        if data_loaded[self.get_key()] == "SourceUnit":
            self._parse_source_unit(data_loaded, filename)
        else:
            logger.error("solc version is not supported")
            return

        for top_level_data in data_loaded[self.get_children()]:
            if top_level_data[self.get_key()] == "ContractDefinition":
                contract = Contract(self._compilation_unit)
                contract_parser = ContractSolc(self, contract, top_level_data)
                if "src" in top_level_data:
                    contract.set_offset(top_level_data["src"], self._compilation_unit)

                self._underlying_contract_to_parser[contract] = contract_parser

            elif top_level_data[self.get_key()] == "PragmaDirective":
                if self._is_compact_ast:
                    pragma = Pragma(top_level_data["literals"])
                else:
                    pragma = Pragma(top_level_data["attributes"]["literals"])
                pragma.set_offset(top_level_data["src"], self._compilation_unit)
                self._compilation_unit.pragma_directives.append(pragma)
            elif top_level_data[self.get_key()] == "ImportDirective":
                if self.is_compact_ast:
                    import_directive = Import(top_level_data["absolutePath"])
                    # TODO investigate unitAlias in version < 0.7 and legacy ast
                    if "unitAlias" in top_level_data:
                        import_directive.alias = top_level_data["unitAlias"]
                else:
                    import_directive = Import(top_level_data["attributes"].get("absolutePath", ""))
                import_directive.set_offset(top_level_data["src"], self._compilation_unit)
                self._compilation_unit.import_directives.append(import_directive)

            elif top_level_data[self.get_key()] == "StructDefinition":
                st = StructureTopLevel()
                st.set_offset(top_level_data["src"], self._compilation_unit)
                st_parser = StructureTopLevelSolc(st, top_level_data, self)

                self._compilation_unit.structures_top_level.append(st)
                self._structures_top_level_parser.append(st_parser)

            elif top_level_data[self.get_key()] == "EnumDefinition":
                # Note enum don't need a complex parser, so everything is directly done
                self._parse_enum(top_level_data)

            elif top_level_data[self.get_key()] == "VariableDeclaration":
                var = TopLevelVariable()
                var_parser = TopLevelVariableSolc(var, top_level_data)
                var.set_offset(top_level_data["src"], self._compilation_unit)

                self._compilation_unit.variables_top_level.append(var)
                self._variables_top_level_parser.append(var_parser)
            elif top_level_data[self.get_key()] == "FunctionDefinition":
                func = FunctionTopLevel(self._compilation_unit)
                func_parser = FunctionSolc(func, top_level_data, None, self)

                self._compilation_unit.functions_top_level.append(func)
                self._functions_top_level_parser.append(func_parser)
                self.add_function_or_modifier_parser(func_parser)

            else:
                raise SlitherException(f"Top level {top_level_data[self.get_key()]} not supported")

    def _parse_source_unit(self, data: Dict, filename: str):
        if data[self.get_key()] != "SourceUnit":
            return  # handle solc prior 0.3.6

        # match any char for filename
        # filename can contain space, /, -, ..
        name_candidates = re.findall("=+ (.+) =+", filename)
        if name_candidates:
            assert len(name_candidates) == 1
            name: str = name_candidates[0]
        else:
            name = filename

        sourceUnit = -1  # handle old solc, or error
        if "src" in data:
            sourceUnit_candidates = re.findall("[0-9]*:[0-9]*:([0-9]*)", data["src"])
            if len(sourceUnit_candidates) == 1:
                sourceUnit = int(sourceUnit_candidates[0])
        if sourceUnit == -1:
            # if source unit is not found
            # We can still deduce it, by assigning to the last source_code added
            # This works only for crytic compile.
            # which used --combined-json ast, rather than --ast-json
            # As a result -1 is not used as index
            if self._compilation_unit.core.crytic_compile is not None:
                sourceUnit = len(self._compilation_unit.core.source_code)

        self._compilation_unit.source_units[sourceUnit] = name
        if os.path.isfile(name) and not name in self._compilation_unit.core.source_code:
            self._compilation_unit.core.add_source_code(name)
        else:
            lib_name = os.path.join("node_modules", name)
            if os.path.isfile(lib_name) and not name in self._compilation_unit.core.source_code:
                self._compilation_unit.core.add_source_code(lib_name)

    # endregion
    ###################################################################################
    ###################################################################################
    # region Analyze
    ###################################################################################
    ###################################################################################

    @property
    def parsed(self) -> bool:
        return self._parsed

    @property
    def analyzed(self) -> bool:
        return self._analyzed

    def parse_contracts(self):  # pylint: disable=too-many-statements,too-many-branches
        if not self._underlying_contract_to_parser:
            logger.info(
                f"No contract were found in {self._compilation_unit.core.filename}, check the correct compilation"
            )
        if self._parsed:
            raise Exception("Contract analysis can be run only once!")

        # First we save all the contracts in a dict
        # the key is the contractid
        for contract in self._underlying_contract_to_parser:
            if (
                contract.name.startswith("SlitherInternalTopLevelContract")
                and not contract.is_top_level
            ):
                raise SlitherException(
                    # region multi-line-string
                    """Your codebase has a contract named 'SlitherInternalTopLevelContract'.
Please rename it, this name is reserved for Slither's internals"""
                    # endregion multi-line
                )
            if contract.name in self._compilation_unit.contracts_as_dict:
                if contract.id != self._compilation_unit.contracts_as_dict[contract.name].id:
                    self._compilation_unit.contract_name_collisions[contract.name].append(
                        contract.source_mapping_str
                    )
                    self._compilation_unit.contract_name_collisions[contract.name].append(
                        self._compilation_unit.contracts_as_dict[contract.name].source_mapping_str
                    )
            else:
                self._contracts_by_id[contract.id] = contract
                self._compilation_unit.contracts_as_dict[contract.name] = contract

        # Update of the inheritance
        for contract_parser in self._underlying_contract_to_parser.values():
            # remove the first elem in linearizedBaseContracts as it is the contract itself
            ancestors = []
            fathers = []
            father_constructors = []
            # try:
            # Resolve linearized base contracts.
            missing_inheritance = False

            for i in contract_parser.linearized_base_contracts[1:]:
                if i in contract_parser.remapping:
                    ancestors.append(
                        self._compilation_unit.get_contract_from_name(contract_parser.remapping[i])
                    )
                elif i in self._contracts_by_id:
                    ancestors.append(self._contracts_by_id[i])
                else:
                    missing_inheritance = True

            # Resolve immediate base contracts
            for i in contract_parser.baseContracts:
                if i in contract_parser.remapping:
                    fathers.append(
                        self._compilation_unit.get_contract_from_name(contract_parser.remapping[i])
                    )
                elif i in self._contracts_by_id:
                    fathers.append(self._contracts_by_id[i])
                else:
                    missing_inheritance = True

            # Resolve immediate base constructor calls
            for i in contract_parser.baseConstructorContractsCalled:
                if i in contract_parser.remapping:
                    father_constructors.append(
                        self._compilation_unit.get_contract_from_name(contract_parser.remapping[i])
                    )
                elif i in self._contracts_by_id:
                    father_constructors.append(self._contracts_by_id[i])
                else:
                    missing_inheritance = True

            contract_parser.underlying_contract.set_inheritance(
                ancestors, fathers, father_constructors
            )

            if missing_inheritance:
                self._compilation_unit.contracts_with_missing_inheritance.add(
                    contract_parser.underlying_contract
                )
                contract_parser.log_incorrect_parsing(f"Missing inheritance {contract_parser}")
                contract_parser.set_is_analyzed(True)
                contract_parser.delete_content()

        contracts_to_be_analyzed = list(self._underlying_contract_to_parser.values())

        # Any contract can refer another contract enum without need for inheritance
        self._analyze_all_enums(contracts_to_be_analyzed)
        # pylint: disable=expression-not-assigned
        [c.set_is_analyzed(False) for c in self._underlying_contract_to_parser.values()]

        libraries = [
            c for c in contracts_to_be_analyzed if c.underlying_contract.contract_kind == "library"
        ]
        contracts_to_be_analyzed = [
            c for c in contracts_to_be_analyzed if c.underlying_contract.contract_kind != "library"
        ]

        # We first parse the struct/variables/functions/contract
        self._analyze_first_part(contracts_to_be_analyzed, libraries)
        # pylint: disable=expression-not-assigned
        [c.set_is_analyzed(False) for c in self._underlying_contract_to_parser.values()]

        # We analyze the struct and parse and analyze the events
        # A contract can refer in the variables a struct or a event from any contract
        # (without inheritance link)
        self._analyze_second_part(contracts_to_be_analyzed, libraries)
        [c.set_is_analyzed(False) for c in self._underlying_contract_to_parser.values()]

        # Then we analyse state variables, functions and modifiers
        self._analyze_third_part(contracts_to_be_analyzed, libraries)

        self._parsed = True

    def analyze_contracts(self):  # pylint: disable=too-many-statements,too-many-branches
        if not self._parsed:
            raise SlitherException("Parse the contract before running analyses")
        self._convert_to_slithir()

        compute_dependency(self._compilation_unit)
        self._compilation_unit.compute_storage_layout()
        self._analyzed = True

    def _analyze_all_enums(self, contracts_to_be_analyzed: List[ContractSolc]):
        while contracts_to_be_analyzed:
            contract = contracts_to_be_analyzed[0]

            contracts_to_be_analyzed = contracts_to_be_analyzed[1:]
            all_father_analyzed = all(
                self._underlying_contract_to_parser[father].is_analyzed
                for father in contract.underlying_contract.inheritance
            )

            if not contract.underlying_contract.inheritance or all_father_analyzed:
                self._analyze_enums(contract)
            else:
                contracts_to_be_analyzed += [contract]

    def _analyze_first_part(
        self,
        contracts_to_be_analyzed: List[ContractSolc],
        libraries: List[ContractSolc],
    ):
        for lib in libraries:
            self._parse_struct_var_modifiers_functions(lib)

        # Start with the contracts without inheritance
        # Analyze a contract only if all its fathers
        # Were analyzed
        while contracts_to_be_analyzed:

            contract = contracts_to_be_analyzed[0]

            contracts_to_be_analyzed = contracts_to_be_analyzed[1:]
            all_father_analyzed = all(
                self._underlying_contract_to_parser[father].is_analyzed
                for father in contract.underlying_contract.inheritance
            )

            if not contract.underlying_contract.inheritance or all_father_analyzed:
                self._parse_struct_var_modifiers_functions(contract)

            else:
                contracts_to_be_analyzed += [contract]

    def _analyze_second_part(
        self,
        contracts_to_be_analyzed: List[ContractSolc],
        libraries: List[ContractSolc],
    ):
        for lib in libraries:
            self._analyze_struct_events(lib)

        self._analyze_top_level_structures()

        # Start with the contracts without inheritance
        # Analyze a contract only if all its fathers
        # Were analyzed
        while contracts_to_be_analyzed:

            contract = contracts_to_be_analyzed[0]

            contracts_to_be_analyzed = contracts_to_be_analyzed[1:]
            all_father_analyzed = all(
                self._underlying_contract_to_parser[father].is_analyzed
                for father in contract.underlying_contract.inheritance
            )

            if not contract.underlying_contract.inheritance or all_father_analyzed:
                self._analyze_struct_events(contract)

            else:
                contracts_to_be_analyzed += [contract]

    def _analyze_third_part(
        self,
        contracts_to_be_analyzed: List[ContractSolc],
        libraries: List[ContractSolc],
    ):
        for lib in libraries:
            self._analyze_variables_modifiers_functions(lib)

        # Start with the contracts without inheritance
        # Analyze a contract only if all its fathers
        # Were analyzed
        while contracts_to_be_analyzed:

            contract = contracts_to_be_analyzed[0]

            contracts_to_be_analyzed = contracts_to_be_analyzed[1:]
            all_father_analyzed = all(
                self._underlying_contract_to_parser[father].is_analyzed
                for father in contract.underlying_contract.inheritance
            )

            if not contract.underlying_contract.inheritance or all_father_analyzed:
                self._analyze_variables_modifiers_functions(contract)

            else:
                contracts_to_be_analyzed += [contract]

    def _analyze_enums(self, contract: ContractSolc):
        # Enum must be analyzed first
        contract.analyze_enums()
        contract.set_is_analyzed(True)

    def _parse_struct_var_modifiers_functions(self, contract: ContractSolc):
        contract.parse_structs()  # struct can refer another struct
        contract.parse_state_variables()
        contract.parse_modifiers()
        contract.parse_functions()
        contract.set_is_analyzed(True)

    def _analyze_struct_events(self, contract: ContractSolc):

        contract.analyze_constant_state_variables()

        # Struct can refer to enum, or state variables
        contract.analyze_structs()
        # Event can refer to struct
        contract.analyze_events()

        contract.analyze_using_for()

        contract.set_is_analyzed(True)

    def _analyze_top_level_structures(self):
        try:
            for struct in self._structures_top_level_parser:
                struct.analyze()
        except (VariableNotFound, KeyError) as e:
            raise SlitherException(f"Missing struct {e} during top level structure analyze") from e

    def _analyze_top_level_variables(self):
        try:
            for var in self._variables_top_level_parser:
                var.analyze(self)
        except (VariableNotFound, KeyError) as e:
            raise SlitherException(f"Missing struct {e} during top level structure analyze") from e

    def _analyze_params_top_level_function(self):
        for func_parser in self._functions_top_level_parser:
            func_parser.analyze_params()
            self._compilation_unit.add_function(func_parser.underlying_function)

    def _analyze_content_top_level_function(self):
        try:
            for func_parser in self._functions_top_level_parser:
                func_parser.analyze_content()
        except (VariableNotFound, KeyError) as e:
            raise SlitherException(f"Missing {e} during top level function analyze") from e

    def _analyze_variables_modifiers_functions(self, contract: ContractSolc):
        # State variables, modifiers and functions can refer to anything

        contract.analyze_params_modifiers()
        contract.analyze_params_functions()
        self._analyze_params_top_level_function()

        contract.analyze_state_variables()

        contract.analyze_content_modifiers()
        contract.analyze_content_functions()
        self._analyze_content_top_level_function()

        contract.set_is_analyzed(True)

    def _convert_to_slithir(self):

        for contract in self._compilation_unit.contracts:
            contract.add_constructor_variables()

            for func in contract.functions + contract.modifiers:
                try:
                    func.generate_slithir_and_analyze()
                except AttributeError:
                    # This can happens for example if there is a call to an interface
                    # And the interface is redefined due to contract's name reuse
                    # But the available version misses some functions
                    self._underlying_contract_to_parser[contract].log_incorrect_parsing(
                        f"Impossible to generate IR for {contract.name}.{func.name}"
                    )

            contract.convert_expression_to_slithir_ssa()

        for func in self._compilation_unit.functions_top_level:
            func.generate_slithir_and_analyze()
            func.generate_slithir_ssa(dict())
        self._compilation_unit.propagate_function_calls()
        for contract in self._compilation_unit.contracts:
            contract.fix_phi()
            contract.update_read_write_using_ssa()

    # endregion
