from typing import List
from slither.detectors.abstract_detector import AbstractDetector, DetectorClassification, Output
from slither.core.scope.scope import FileScope

# pylint: disable=protected-access,too-many-nested-blocks
class UnusedImport(AbstractDetector):
    """
    Detector unused imports.
    """

    ARGUMENT = "unused-import"
    HELP = "Detects unused imports"
    IMPACT = DetectorClassification.INFORMATIONAL
    CONFIDENCE = DetectorClassification.HIGH

    WIKI = "https://github.com/crytic/slither/wiki/Detector-Documentation#unused-imports"

    WIKI_TITLE = "Unused Imports"
    WIKI_DESCRIPTION = "Importing a file that is not used in the contract likely indicates a mistake. The import should be removed until it is needed."

    # region wiki_exploit_scenario
    WIKI_EXPLOIT_SCENARIO = """
    ```solidity
    import {A} from "./A.sol";
    contract B {}
    ```
    B either should import from A and it was forgotten or the import is not needed and should be removed.
    """
    # endregion wiki_exploit_scenario
    WIKI_RECOMMENDATION = (
        "Remove the unused import. If the import is needed later, it can be added back."
    )

    @staticmethod
    def _is_import_container(scope: FileScope) -> bool:  # pylint: disable=too-many-branches
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
        for ct in scope.type_aliases.values():
            if ct.source_mapping and ct.source_mapping.filename == scope.filename:
                return False
        for uf in scope.using_for_directives:
            if uf.file_scope == scope:
                return False
        for v in scope.variables.values():
            if v.file_scope == scope:
                return False
        return True

    def _detect(self) -> List[Output]:  # pylint: disable=too-many-branches
        results: List[Output] = []
        # This is computed lazily and then memoized so we need to trigger the computation.
        self.slither._compute_offsets_to_ref_impl_decl()

        for unit in self.slither.compilation_units:
            for filename, current_scope in unit.scopes.items():
                # Skip files that are dependencies
                if unit.crytic_compile.is_dependency(filename.absolute):
                    continue

                unused_list = []
                for i in current_scope.imports:
                    # `scope.imports` contains all transitive imports so we need to filter out imports not explicitly imported in the file.
                    # Otherwise, we would recommend removing an import that is used by a leaf contract and cause compilation errors.
                    if i.scope != current_scope:
                        continue

                    # If a scope doesn't define any contract, function, etc., it is an import container.
                    # The second case accounts for importing from an import container as a reference will only be in the definition's file.
                    if self._is_import_container(i.scope) or self._is_import_container(
                        unit.get_scope(i.filename)
                    ):
                        continue

                    imported_path = self.slither.crytic_compile.filename_lookup(i.filename)

                    use_found = False
                    # Search through all references to the imported file
                    for _, refs_to_imported_path in self.slither._offset_to_references[
                        imported_path
                    ].items():
                        for ref in refs_to_imported_path:
                            # If there is a reference in this file to the imported file, it is used.
                            if ref.filename == filename:
                                use_found = True
                                break

                        if use_found:
                            break

                    if not use_found:
                        unused_list.append(f"{i.source_mapping.content} ({i.source_mapping})")

                if len(unused_list) > 0:
                    info = [
                        f"The following unused import(s) in {filename.used} should be removed:",
                    ]
                    for unused in unused_list:
                        info += ["\n\t-", unused, "\n"]

                    results.append(self.generate_result(info))

        return results
