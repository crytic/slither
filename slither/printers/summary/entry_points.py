"""
Module printing all the entry points of the contracts

This printer identifies and displays all externally accessible functions (entry points)
of smart contracts, excluding view/pure functions and special functions like constructors.
It helps in security analysis by providing a clear overview of possible external interactions.
"""
from slither.printers.abstract_printer import AbstractPrinter
from slither.core.declarations.function_contract import FunctionContract
from slither.core.declarations.contract import Contract
from slither.utils.colors import Colors
from slither.utils.output import Output

class PrinterEntryPoints(AbstractPrinter):
    ARGUMENT = "entry-points"
    HELP = "Print the entry points of the contracts"

    WIKI = "https://github.com/trailofbits/slither/wiki/Printer-documentation#entry-points"

    def _get_contract_type(self, contract: Contract) -> str:
        """
        Returns a string describing the contract type.
        
        Args:
            contract (Contract): The contract to analyze
            
        Returns:
            str: Contract type description ("Interface", "Library", "Abstract Contract", or "Contract")
        """
        if contract.is_interface:
            return "Interface"
        if contract.is_library:
            return "Library"
        if contract.is_abstract:
            return "Abstract Contract"
        return "Contract"

    def output(self, filename: str) -> Output:
        """
        Generates a formatted output of all contract entry points.
        
        This method processes all contracts to:
        1. Filter out interfaces and contracts from utility/testing directories
        2. Sort contracts by type and name
        3. Identify and format public/external functions
        4. Include inheritance and modifier information
        
        Args:
            filename (str): The filename to save the results (not used in current implementation)
            
        Returns:
            Output: Formatted data containing entry points for each contract
        """
        all_contracts = []

        # Filter out interfaces and contracts from utility/testing directories
        non_interface_contracts = [
            c for c in self.contracts 
            if not c.is_interface and 
            'lib/' not in c.source_mapping.filename.absolute and
            'node_modules/' not in c.source_mapping.filename.absolute and
            'mock/' not in c.source_mapping.filename.absolute
        ]
        
        # Sort contracts with priority: regular contracts > abstract contracts > libraries
        sorted_contracts = sorted(
            non_interface_contracts,
            key=lambda x: (
                not x.is_library,    # Libraries last
                not x.is_abstract,   # Abstract contracts second
                x.name              # Alphabetical within each category
            )
        )

        for contract in sorted_contracts:
            # Identify entry points: public/external functions excluding:
            # - Constructors, fallback, receive functions
            # - View/pure functions
            # - Interface functions
            entry_points = [f for f in contract.functions if 
                          (f.visibility in ['public', 'external'] and 
                           isinstance(f, FunctionContract) and
                           not f.is_constructor and
                           not f.is_fallback and
                           not f.is_receive and
                           not f.view and
                           not f.pure and
                           not f.contract_declarer.is_interface)]
            
            # Skip contract if no entry points
            if not entry_points:
                continue
            
            contract_info = []
            contract_type = self._get_contract_type(contract)
            source_file = contract.source_mapping.filename.short
            
            # Combine contract type, name, and source into one line
            contract_info.append(f"\n{contract_type} {Colors.BOLD}{Colors.BLUE}{contract.name}{Colors.END} ({source_file})")
            
            # Add inheritance information if any
            if contract.inheritance:
                inheritance_str = ", ".join(c.name for c in contract.inheritance)
                contract_info.append(f"Inherits from: {inheritance_str}")
            
            # Sort functions prioritizing external over public visibility
            entry_points.sort(key=lambda x: (x.visibility != 'external', x.visibility != 'public', x.full_name))
            
            for f in entry_points:
                # Collect and format modifier information
                modifiers = [m.name for m in f.modifiers] if f.modifiers else []
                modifier_str = f" [{', '.join(modifiers)}]" if modifiers else ""
                
                # Identify inherited functions and their origin
                inherited_str = ""
                if f.contract_declarer != contract:
                    inherited_str = f" (from {f.contract_declarer.name})"
                
                # Extract just the function name without parameters
                function_name = f.name
                
                contract_info.append(f"        - {Colors.BOLD}{Colors.RED}{function_name}{Colors.END}{modifier_str}{inherited_str}")
            
            all_contracts.append("\n".join(contract_info))
        
        # Generate final output
        info = "\n".join(all_contracts) if all_contracts else ""
        self.info(info)
        
        return self.generate_output(info)