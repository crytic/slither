"""
Module printing ERC token standard detection results.

Automatically identifies and classifies token contracts based on their
implemented interfaces, supporting ERC-20, ERC-721, ERC-777, ERC-1155,
and ERC-4626 standards.
"""

from slither.printers.abstract_printer import AbstractPrinter
from slither.utils.colors import green, yellow, red, blue, bold
from slither.utils.myprettytable import MyPrettyTable
from slither.utils.output import Output
from slither.utils.erc import ERCS, erc_to_signatures


# Token standards to detect (subset of ERCS focused on tokens)
TOKEN_STANDARDS = {
    "ERC-20": "ERC20",
    "ERC-721": "ERC721",
    "ERC-777": "ERC777",
    "ERC-1155": "ERC1155",
    "ERC-4626": "ERC4626",
}


class ERCPrinter(AbstractPrinter):
    ARGUMENT = "erc"
    HELP = "Detect and classify ERC token contracts (ERC-20, ERC-721, ERC-777, ERC-1155, ERC-4626)"

    WIKI = "https://github.com/trailofbits/slither/wiki/Printer-documentation#erc"

    def _get_compliance(
        self, contract, erc_key: str
    ) -> tuple[float, list[str], list[str]]:
        """
        Calculate compliance percentage for a given ERC standard.

        Uses the ERCS dictionary from slither.utils.erc for standard definitions.

        Returns:
            Tuple of (compliance_percentage, implemented_signatures, missing_signatures)
        """
        erc_functions, _ = ERCS[erc_key]
        required_sigs = erc_to_signatures(erc_functions)
        contract_sigs = contract.functions_signatures

        implemented = [sig for sig in required_sigs if sig in contract_sigs]
        missing = [sig for sig in required_sigs if sig not in contract_sigs]

        compliance = len(implemented) / len(required_sigs) * 100 if required_sigs else 0
        return compliance, implemented, missing

    def _check_events(self, contract, erc_key: str) -> tuple[list[str], list[str]]:
        """Check which ERC events are implemented for a given standard."""
        _, erc_events = ERCS[erc_key]

        contract_event_sigs = [
            f"{e.name}({','.join(str(p.type) for p in e.elems)})"
            for e in contract.events
        ]

        implemented = []
        missing = []
        for event in erc_events:
            event_sig = f"{event.name}({','.join(event.parameters)})"
            if event_sig in contract_event_sigs:
                implemented.append(event_sig)
            else:
                missing.append(event_sig)

        return implemented, missing

    def _is_fully_compliant(self, contract, erc_key: str) -> bool:
        """Check if contract implements all required functions for a standard."""
        erc_functions, _ = ERCS[erc_key]
        required_sigs = erc_to_signatures(erc_functions)
        contract_sigs = contract.functions_signatures
        return all(sig in contract_sigs for sig in required_sigs)

    def _confidence_label(self, compliance: float) -> str:
        """Return colored confidence label based on compliance percentage."""
        if compliance >= 100:
            return green("HIGH (100%)")
        if compliance >= 80:
            return green(f"HIGH ({compliance:.0f}%)")
        if compliance >= 50:
            return yellow(f"MEDIUM ({compliance:.0f}%)")
        return red(f"LOW ({compliance:.0f}%)")

    def _analyze_contract(self, contract) -> dict | None:
        """Analyze a single contract for ERC compliance."""
        # Skip interfaces, libraries, and abstract contracts
        if contract.is_interface or contract.is_library:
            return None

        results = {
            "name": contract.name,
            "source": (
                contract.source_mapping.filename.short
                if contract.source_mapping
                else "unknown"
            ),
            "types": [],
            "details": {},
        }

        # Check each token standard
        for display_name, erc_key in TOKEN_STANDARDS.items():
            if self._is_fully_compliant(contract, erc_key):
                compliance, implemented, missing = self._get_compliance(
                    contract, erc_key
                )
                events_impl, events_missing = self._check_events(contract, erc_key)
                results["types"].append(display_name)
                results["details"][display_name] = {
                    "compliance": compliance,
                    "implemented": implemented,
                    "missing": missing,
                    "events_implemented": events_impl,
                    "events_missing": events_missing,
                }

        # Check for partial implementations (>= 30% compliance but not fully compliant)
        if not results["types"]:
            partial_types = []
            for display_name, erc_key in TOKEN_STANDARDS.items():
                compliance, _, _ = self._get_compliance(contract, erc_key)
                if compliance >= 30:
                    partial_types.append(f"{display_name} ({compliance:.0f}%)")

            if partial_types:
                results["partial"] = partial_types

        if results["types"] or results.get("partial"):
            return results

        return None

    def _format_contract_details(
        self, result: dict, standard: str, show_header: bool = True
    ) -> str:
        """Format detailed output for a contract implementing a standard."""
        txt = ""
        details = result["details"][standard]

        txt += f"\n{green(result['name'])} ({result['source']})\n"
        txt += f"  Confidence: {self._confidence_label(details['compliance'])}\n"

        total_funcs = len(details["implemented"]) + len(details["missing"])
        txt += f"  Functions: {len(details['implemented'])}/{total_funcs}\n"

        if details["missing"]:
            missing_display = ", ".join(details["missing"][:3])
            txt += f"  Missing: {missing_display}"
            if len(details["missing"]) > 3:
                txt += f" (+{len(details['missing']) - 3} more)"
            txt += "\n"

        total_events = len(details["events_implemented"]) + len(
            details["events_missing"]
        )
        if total_events > 0:
            txt += (
                f"  Events: {len(details['events_implemented'])}/{total_events}\n"
            )

        return txt

    def output(self, _filename: str) -> Output:
        """Generate ERC token detection output."""
        txt = ""

        # Categorize contracts by token standard
        contracts_by_standard: dict[str, list[dict]] = {
            name: [] for name in TOKEN_STANDARDS
        }
        partial_contracts: list[dict] = []

        # Analyze all contracts
        for contract in self.contracts:
            result = self._analyze_contract(contract)
            if result:
                for standard in result["types"]:
                    contracts_by_standard[standard].append(result)
                if result.get("partial") and not result["types"]:
                    partial_contracts.append(result)

        txt += bold(blue("\nERC Token Detection Results\n"))
        txt += "=" * 50 + "\n"

        # Summary table
        summary_table = MyPrettyTable(["Token Standard", "Contracts Found"])
        total_tokens = 0
        for display_name in TOKEN_STANDARDS:
            count = len(contracts_by_standard[display_name])
            if count > 0:
                summary_table.add_row([display_name, str(count)])
                total_tokens += count

        if partial_contracts:
            summary_table.add_row(
                ["Partial Implementations", str(len(partial_contracts))]
            )

        txt += "\n" + str(summary_table) + "\n"

        # Standard descriptions for headers
        standard_descriptions = {
            "ERC-20": "ERC-20 Tokens (Fungible)",
            "ERC-721": "ERC-721 Tokens (NFTs)",
            "ERC-777": "ERC-777 Tokens (Advanced Fungible)",
            "ERC-1155": "ERC-1155 Tokens (Multi-Token)",
            "ERC-4626": "ERC-4626 Vaults (Tokenized Vaults)",
        }

        # Detailed output for each token type
        for display_name in TOKEN_STANDARDS:
            contracts = contracts_by_standard[display_name]
            if contracts:
                desc = standard_descriptions.get(display_name, display_name)
                txt += bold(blue(f"\n{desc}\n"))
                txt += "-" * 30 + "\n"
                for result in contracts:
                    txt += self._format_contract_details(result, display_name)

        # Partial implementations
        if partial_contracts:
            txt += bold(yellow("\nPartial/Non-Standard Implementations\n"))
            txt += "-" * 30 + "\n"
            for result in partial_contracts:
                txt += f"\n{yellow(result['name'])} ({result['source']})\n"
                txt += f"  Appears to be: {', '.join(result['partial'])}\n"

        if total_tokens == 0 and not partial_contracts:
            txt += "\nNo ERC token contracts detected.\n"

        # Statistics
        txt += bold(blue("\nStatistics\n"))
        txt += "-" * 30 + "\n"
        txt += f"Total contracts analyzed: {len(self.contracts)}\n"
        txt += f"Token contracts found: {total_tokens}\n"
        if partial_contracts:
            txt += f"Partial implementations: {len(partial_contracts)}\n"

        self.info(txt)

        # Build JSON output
        res = self.generate_output(txt)

        json_output = {
            "tokens": {},
            "partial": [
                {
                    "contract": r["name"],
                    "source": r["source"],
                    "detected_types": r["partial"],
                }
                for r in partial_contracts
            ],
            "statistics": {
                "total_contracts": len(self.contracts),
                "token_contracts": total_tokens,
                "partial_implementations": len(partial_contracts),
            },
        }

        # Add each standard's contracts to JSON
        for display_name, erc_key in TOKEN_STANDARDS.items():
            contracts = contracts_by_standard[display_name]
            if contracts:
                json_output["tokens"][display_name] = [
                    {
                        "contract": r["name"],
                        "source": r["source"],
                        "compliance": r["details"][display_name]["compliance"],
                        "missing_functions": r["details"][display_name]["missing"],
                        "missing_events": r["details"][display_name]["events_missing"],
                    }
                    for r in contracts
                ]

        res.add_other("token_detection", json_output)

        return res
