from logging import Logger
from pathlib import PurePath
from typing import Dict, Set, TYPE_CHECKING, List

from crytic_compile.utils.naming import Filename

from slither.core.compilation_unit import SlitherCompilationUnit
from slither.core.declarations import Contract
from slither.core.scope.scope import FileScope
from slither.core.solidity_types import TypeAliasTopLevel, TypeAliasContract
from slither.core.source_mapping.source_mapping import SourceMapping
from slither.core.variables.variable import Variable
from slither.detectors.abstract_detector import (
    AbstractDetector,
    DetectorClassification,
    DETECTOR_INFO,
)
from slither.utils.output import Output

if TYPE_CHECKING:
    from slither import Slither


class UnusedImports(AbstractDetector):
    """
    Unused imports detector
    """

    ARGUMENT = "unused-imports"
    HELP = "Detect unused imports"
    IMPACT = DetectorClassification.INFORMATIONAL
    CONFIDENCE = DetectorClassification.HIGH

    WIKI = "https://github.com/crytic/slither/wiki/Detector-Documentation#unused-imports"

    WIKI_TITLE = "Unused imports"
    WIKI_DESCRIPTION = (
        "Detects imports that are not used by source files. Currently, files with cyclic imports and files with "
        "'import {...} from' directives are not supported."
    )
    WIKI_RECOMMENDATION = "Remove unused imports"

    analysed_files: Set[str] = set()
    import_containers: Set[str] = set()

    def __init__(
        self, compilation_unit: SlitherCompilationUnit, slither: "Slither", logger: Logger
    ):
        super().__init__(compilation_unit, slither, logger)
        self.needed_imports = self._new_dict()
        self.actual_imports = self._new_dict()
        self.absolute_path_to_imp_filename: Dict[str, str] = {}
        self.imports_cycle_detected = False

    # pylint: disable=too-many-branches
    @staticmethod
    def _is_import_container(scope: FileScope) -> bool:
        """
        Returns True if a given file (provided as a `FileScope` object) contains only `import` directives (and pragmas).
        Such a file doesn't need the imports it contains, but its purpose is to aggregate certain correlated imports.
        """
        for c in scope.contracts.values():
            if c.file_scope == scope:
                return False
        for err in scope.custom_errors:
            if err.file_scope == scope:
                return False
        for en in scope.enums.values():
            if en.file_scope == scope:
                return False
        for f in scope.functions:
            if f.file_scope == scope:
                return False
        for st in scope.structures.values():
            if st.file_scope == scope:
                return False
        for ct in scope.user_defined_types.values():
            if ct.source_mapping and ct.source_mapping.filename == scope.filename:
                return False
        for uf in scope.using_for_directives:
            if uf.file_scope == scope:
                return False
        for v in scope.variables.values():
            if v.file_scope == scope:
                return False
        return True

    @staticmethod
    def _update_import_containers(scopes: Dict[Filename, FileScope]) -> None:
        """
        Updates `import_containers` set by adding "import containers" (files containing only `import` statements) from
        the current scope.
        """
        for name, scope in scopes.items():
            if UnusedImports._is_import_container(scope):
                UnusedImports.import_containers.add(name.absolute)

    def _dfs(self, graph: Dict[str, Set[str]], color: Dict[str, int], x: str) -> None:
        """
        Simple DFS that checks for a cycle in a given graph.
        """
        color[x] = 1
        for v in graph[x]:
            if color[v] == 0:
                self._dfs(graph, color, v)
            elif color[v] == 1:
                self.imports_cycle_detected = True
        color[x] = 2

    def _detect_cycles(self, graph: Dict[str, Set[str]]) -> None:
        """
        Detects cycle in a directed graph.
        """
        vertex_color: Dict[str, int] = {}
        for k in graph.keys():
            vertex_color[k] = 0
        for k in graph.keys():
            for v in graph[k]:
                if vertex_color[v] == 0:
                    self._dfs(graph, vertex_color, v)
                if self.imports_cycle_detected:
                    return

    def _new_dict(self) -> Dict[str, Set[str]]:
        """
        Helper method. Creates a dictionary with all input files as keys and empty sets as values.
        """
        dictionary: Dict[str, Set[str]] = {}
        for file in self.compilation_unit.scopes:
            dictionary[file.absolute] = set()
        return dictionary

    def _import_to_absolute_path(self, imp: str) -> str:
        """
        Converts an import to the absolute path of that import.
        Useful for cases like "import @openzeppelin/...".
        """
        return self.compilation_unit.crytic_compile.filename_lookup(imp).absolute

    @staticmethod
    def _add_import(imps: Dict[str, Set[str]], key: str, value: str) -> None:
        """
        Adds import entries to imps dict.
        Keys are absolute paths to files (as strings) and each key points to a set of absolute paths (as strings).
        """
        if key == value:
            return
        imps[key].add(value)

    def _add_custom_type(self, v: Variable) -> None:
        """
        Adds user defined types to self.needed_imports.
        """
        assert v.source_mapping

        if isinstance(v.type, (TypeAliasTopLevel, TypeAliasContract)):
            assert v.type.source_mapping
            self._add_import(
                self.needed_imports,
                v.source_mapping.filename.absolute,
                v.type.source_mapping.filename.absolute,
            )

    def _add_item_by_references(self, item: SourceMapping) -> None:
        """
        Adds all uses of item to self.needed_imports by its references.
        """
        assert item.source_mapping
        for ref in item.references:
            self._add_import(
                self.needed_imports, ref.filename.absolute, item.source_mapping.filename.absolute
            )

    def _initialise_actual_imports(self) -> None:
        """
        After running this function, self.actual_imports contains, for each file, a set of files imported by it.
        """
        for imp in self.compilation_unit.import_directives:
            import_path = self._import_to_absolute_path(imp.filename)
            assert imp.source_mapping
            self._add_import(self.actual_imports, imp.source_mapping.filename.absolute, import_path)

    def _initialise_absolute_path_to_imp_filename(self) -> None:
        for imp in self.compilation_unit.import_directives:
            import_path = self._import_to_absolute_path(imp.filename)
            self.absolute_path_to_imp_filename[import_path] = imp.filename

    def _find_top_level_structs_uses(self) -> None:
        """
        For each top level struct, analyse all of its uses.
        """
        for st in self.compilation_unit.structures_top_level:
            self._add_item_by_references(st)

    def _find_top_level_custom_types_uses(self) -> None:
        """
        For each top level user defined type, analyse all of its uses.
        """
        for _, ct in self.compilation_unit.user_defined_value_types.items():
            self._add_item_by_references(ct)

    def _find_top_level_enums_uses(self) -> None:
        """
        For each top level enum, analyse all of its uses.
        """
        for en in self.compilation_unit.enums_top_level:
            self._add_item_by_references(en)

    def _find_top_level_constants_uses(self) -> None:
        """
        For each top level constant, analyse all of its uses.
        """
        for var in self.compilation_unit.variables_top_level:
            self._add_item_by_references(var)

    def _find_top_level_custom_errors_uses(self) -> None:
        """
        For each top level custom error, analyse all of its uses.
        """
        for err in self.compilation_unit.custom_errors:
            self._add_item_by_references(err)

    def _find_top_level_functions_uses(self) -> None:
        """
        For each top level function, analyse all of its uses.
        """
        for f in self.compilation_unit.functions_top_level:
            self._add_item_by_references(f)

    def _find_top_level_items_uses(self) -> None:
        """
        Finds all uses of top level items, excluding contracts, libraries and interfaces.
        These include:
        - structs
        - custom types (only top level uses, but all custom types, possibly contract level)
        - enums
        - constants
        - custom errors
        - functions
        It's not possible to declare top level variables (not constants), events and modifiers at the moment.
        """
        self._find_top_level_structs_uses()
        self._find_top_level_custom_types_uses()
        self._find_top_level_enums_uses()
        self._find_top_level_constants_uses()
        self._find_top_level_custom_errors_uses()
        self._find_top_level_functions_uses()

    def _find_contract_level_structs_uses(self, c: Contract) -> None:
        """
        For each contract level struct, analyse all of its uses.
        """
        for st in c.structures:
            self._add_item_by_references(st)

    def _find_contract_level_custom_types_uses(self, c: Contract) -> None:
        """
        For each contract level user defined type, analyse all of its uses.
        """
        for _, ct in c.file_scope.user_defined_types.items():
            self._add_item_by_references(ct)

    def _find_contract_level_enums_uses(self, c: Contract) -> None:
        """
        For each contract level enum, analyse all of its uses.
        """
        for en in c.enums:
            self._add_item_by_references(en)

    def _find_contract_level_variables_uses(self, c: Contract) -> None:
        """
        For each contract level variable, analyse all of its uses.
        """
        for var in c.variables:
            self._add_item_by_references(var)

    def _find_contract_level_custom_errors_uses(self, c: Contract) -> None:
        """
        For each contract level custom error, analyse all of its uses.
        """
        for err in c.custom_errors:
            self._add_item_by_references(err)

    def _find_contract_level_functions_and_modifiers_uses(self, c: Contract) -> None:
        """
        For each contract level function / modifier, analyse all of its uses.
        """
        for fm in c.functions_and_modifiers:
            # the following line is needed since a non-private function / modifier will be present in derived contracts,
            # so, they are needed, but that isn't reflected in fm.references
            assert fm.source_mapping
            self._add_import(
                self.needed_imports,
                fm.file_scope.filename.absolute,
                fm.source_mapping.filename.absolute,
            )
            if len(fm.functions_shadowed) == 0:
                self._add_item_by_references(fm)
            else:
                # function `fm` is overriding some other (virtual) functions
                # it means that its references list will contain all usages of these virtual functions
                # but if they are referenced, it doesn't necessarily mean that `fm` is referenced
                # so we are adding only references of `fm` that aren't references to virtual functions it overrides
                references = set(fm.references)
                for f in fm.functions_shadowed:
                    references -= set(f.references)
                for ref in references:
                    self._add_import(
                        self.needed_imports,
                        ref.filename.absolute,
                        fm.source_mapping.filename.absolute,
                    )

    def _find_contract_level_custom_events_uses(self, c: Contract) -> None:
        """
        For each custom event (cannot be top level at the moment), analyse all of its uses.
        """
        for ev in c.events:
            self._add_item_by_references(ev)

    def _find_contract_level_items_uses(self) -> None:
        """
        Finds all uses of items in contracts, libraries and interfaces.
        These include:
        - structs
        - custom types (only contract level uses, but all custom types, possibly top level)
        - enums
        - variables
        - custom errors
        - functions and modifiers
        - custom events
        - contracts, libraries and interfaces themselves
        """
        for c in self.compilation_unit.contracts:
            self._find_contract_level_structs_uses(c)
            self._find_contract_level_custom_types_uses(c)
            self._find_contract_level_enums_uses(c)
            self._find_contract_level_variables_uses(c)
            self._find_contract_level_custom_errors_uses(c)
            self._find_contract_level_functions_and_modifiers_uses(c)
            self._find_contract_level_custom_events_uses(c)
            # the following line is needed since if we have contract A and some function A.fun, then, when called in B
            # (by "A.fun()"), the fun's references list isn't updated. Instead, the A's references list is updated. The
            # same is true for errors defined in contracts.
            self._add_item_by_references(c)
            # the following loop is needed since if we have an empty contract A and contract B inheriting from A,
            # then it's not reflected in A's references
            assert c.source_mapping
            for p in c.inheritance:
                assert p.source_mapping
                self._add_import(
                    self.needed_imports,
                    c.source_mapping.filename.absolute,
                    p.source_mapping.filename.absolute,
                )

    @staticmethod
    def _add_all_imports_for_file(
        actual_imports: Dict[str, Set[str]], all_imports: Dict[str, Set[str]], file: str
    ) -> None:
        """
        For a certain file, adds all files from its import graph to all_imports, including files imported indirectly.
        For instance, if we have:
            E.sol:
                import "./D.sol"
                import "./C.sol"
            C.sol:
                import "./B.sol"
            B.sol:
                import "./A.sol"
        then the function, called for E.sol will add {A.sol, B.sol, C.sol, D.sol} to all_imports[E.sol].
        """
        for v in actual_imports[file]:
            if len(all_imports[v]) == 0:  # either not yet analysed or analysed and empty
                UnusedImports._add_all_imports_for_file(actual_imports, all_imports, v)
            for imp in all_imports[v]:
                UnusedImports._add_import(all_imports, file, imp)

        for imp in actual_imports[file]:
            UnusedImports._add_import(all_imports, file, imp)

    def _get_all_imports(self) -> Dict[str, Set[str]]:
        """
        Returns a dict, that for each file contains all files from its import graph, including files imported
        indirectly.
        For instance, if we have:
            E.sol:
                import "./D.sol"
                import "./C.sol"
            C.sol:
                import "./B.sol"
            B.sol:
                import "./A.sol"
        the function will return the following dictionary:
        {
            A.sol: {}
            B.sol: {A.sol}
            C.sol: {A.sol, B.sol}
            D.sol: {}
            E.sol: {A.sol, B.sol, C.sol, D.sol}
        }
        """
        all_imports = self._new_dict()
        for k, _ in self.actual_imports.items():
            UnusedImports._add_all_imports_for_file(self.actual_imports, all_imports, k)
        return all_imports

    def _get_all_imports_in_needed(self, all_imports: Dict[str, Set[str]]) -> Dict[str, Set[str]]:
        """
        Returns a dict, that for each file, holds all files imported directly or indirectly by any of imports that this
        file needs.
        For instance, if we have:
            D.sol:
                import B.sol // needed
                import C.sol // unneeded
            B.sol:
                import A.sol
        then all_imports_in_needed[D.sol] = {A.sol}.

        The idea here is that, if file D.sol has to import B.sol, it automatically imports all of B's imports.
        So, if D.sol needs A.sol as well, we won't recommend adding A.sol to D's imports, because it imports it
        indirectly by importing B.sol.
        But, if on the other hand, B.sol isn't needed in D.sol, but A.sol is, then all_imports_in_needed[D.sol] = {},
        hence we will recommend importing A.sol (since it won't be imported indirectly) and removing B.sol from imports.
        """
        all_imports_in_needed = self._new_dict()
        for k, imps in self.needed_imports.items():
            for imp in imps:
                all_imports_in_needed[k] |= all_imports[imp]
        return all_imports_in_needed

    def _remove_redundant_imports_from_needed(self, all_imports: Dict[str, Set[str]]) -> None:
        """
        Removes some imports from the needed_imports dict. The resulting dict, for each key k, contains the smallest
        number of items such that the following equality holds:
            all_imports[old_needed_imports[k]] = all_imports[new_needed_imports[k]],
        where old_needed_imports is needed_imports before the function call and new_needed_imports - after the call.
        The reasoning behind this is, that as long as the above equality holds, we can remove some imports from
        needed_imports, while still importing the same set of files.
        For instance, consider the following example:
            C.sol:
                import B.sol // B.sol needed
                import A.sol // A.sol needed
            B.sol:
                import A.sol
        Before the function call, needed_imports[C.sol] = {A.sol, B.sol}, since both files are used in C.sol.
        However, by importing B.sol, C.sol automatically imports A.sol as well, so it doesn't need to import A.sol
        directly. So, after the call: needed_imports[C.sol] = {B.sol}.
        """
        for _, vs in self.needed_imports.items():
            to_remove: Set[str] = set()
            for v in vs:
                to_remove |= all_imports[v]
            for imp in to_remove:
                if imp in vs:
                    vs.remove(imp)

    def _get_needed_but_not_imported_directly(self) -> Dict[str, Set[str]]:
        """
        Returns a dict, that for each file, contains files that are needed by it, but not imported directly (via
        "import" statement). These files can, however, be imported indirectly.
        For instance, if we have:
            C.sol
                import B.sol // unneeded, but something from A.sol is used somewhere in C.sol
            B.sol:
                import A.sol
        then needed_but_not_imported_directly[C.sol] = {A.sol}, even though A.sol is imported indirectly in C.sol using
        "import B.sol".
        """
        needed_but_not_imported_directly = self._new_dict()
        for k, v in self.needed_imports.items():
            needed_but_not_imported_directly[k] = v - self.actual_imports[k]
        return needed_but_not_imported_directly

    def _get_imported_but_unneeded(self) -> Dict[str, Set[str]]:
        """
        Returns a dict, that for each file, contains files that are directly imported by it (via "import" statement),
        but are not needed (even, if their own imports are needed).
        For instance, if we have:
            C.sol:
                import B.sol // unneeded, but something from A.sol is used somewhere in C.sol
            B.sol:
                import A.sol
        then imported_but_unneeded[C.sol] = {B.sol}, even though A.sol is needed and imported indirectly in C.sol using
        "import B.sol".
        """
        imported_but_unneeded = self._new_dict()
        for k, v in self.actual_imports.items():
            imported_but_unneeded[k] = v - self.needed_imports[k]
        return imported_but_unneeded

    def _detect(self) -> List[Output]:
        results: List[Output] = []

        UnusedImports._update_import_containers(self.compilation_unit.scopes)
        self._initialise_absolute_path_to_imp_filename()
        self._initialise_actual_imports()
        self._find_top_level_items_uses()
        self._find_contract_level_items_uses()

        self._detect_cycles(self.actual_imports)
        if self.imports_cycle_detected:
            # no support for cycles in import graph at the moment
            return results

        all_imports = self._get_all_imports()
        all_imports_in_needed = self._get_all_imports_in_needed(all_imports)
        self._remove_redundant_imports_from_needed(all_imports)

        needed_but_not_imported_directly = self._get_needed_but_not_imported_directly()
        imported_but_unneeded = self._get_imported_but_unneeded()

        for k, v in imported_but_unneeded.items():
            info: DETECTOR_INFO = []
            output = ""
            if k in UnusedImports.analysed_files or len(v) == 0:
                continue
            if k in UnusedImports.import_containers:
                continue
            output += "Unused imports found in " + PurePath(k).as_posix() + ".\n"
            output += "Consider removing the following imports:\n"
            for imp in v:
                output += PurePath(self.absolute_path_to_imp_filename[imp]).as_posix()
                output += "\n"
            if (
                len(needed_but_not_imported_directly[k]) > 0
                and len(needed_but_not_imported_directly[k] - all_imports_in_needed[k]) > 0
            ):
                output += "and adding the following:\n"
                for imp in needed_but_not_imported_directly[k]:
                    if imp in self.absolute_path_to_imp_filename:
                        output += PurePath(self.absolute_path_to_imp_filename[imp]).as_posix()
                    else:
                        # possible since `self.absolute_path_to_imp_filename` contains only existing imports, and it is
                        # possible for the detector to recommend adding a different import
                        output += PurePath(imp).as_posix()
                    output += "\n"
            if output != "":
                output += "\n"
            info.append(output)
            res = self.generate_result(info)
            results.append(res)

        for file in self.compilation_unit.scopes:
            UnusedImports.analysed_files.add(file.absolute)

        return results
