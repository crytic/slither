""""
    Contract module
"""
import logging
from slither.core.children.child_slither import ChildSlither
from slither.core.source_mapping.source_mapping import SourceMapping
from slither.core.declarations.function import Function
from slither.utils.erc import ERC20_signatures, \
    ERC165_signatures, ERC223_signatures, ERC721_signatures, \
    ERC1820_signatures, ERC777_signatures

logger = logging.getLogger("Contract")

class Contract(ChildSlither, SourceMapping):
    """
    Contract class
    """

    def __init__(self):
        super(Contract, self).__init__()
        self._name = None

        self._name = None
        self._id = None
        self._inheritance = [] # all contract inherited, c3 linearization
        self._immediate_inheritance = [] # immediate inheritance

        # Constructors called on contract's definition
        # contract B is A(1) { ..
        self._explicit_base_constructor_calls = []

        self._enums = {}
        self._structures = {}
        self._events = {}
        self._variables = {}
        self._modifiers = {}
        self._functions = {}
        self._using_for = {}
        self._kind = None

        self._signatures = None


        self._initial_state_variables = [] # ssa

    ###################################################################################
    ###################################################################################
    # region General's properties
    ###################################################################################
    ###################################################################################

    @property
    def name(self):
        """str: Name of the contract."""
        return self._name

    @property
    def id(self):
        """Unique id."""
        return self._id

    @property
    def contract_kind(self):
        return self._kind

    # endregion
    ###################################################################################
    ###################################################################################
    # region Structures
    ###################################################################################
    ###################################################################################

    @property
    def structures(self):
        '''
            list(Structure): List of the structures
        '''
        return list(self._structures.values())

    def structures_as_dict(self):
        return self._structures

    # endregion
    ###################################################################################
    ###################################################################################
    # region Enums
    ###################################################################################
    ###################################################################################

    @property
    def enums(self):
        return list(self._enums.values())

    def enums_as_dict(self):
        return self._enums

    # endregion
    ###################################################################################
    ###################################################################################
    # region Events
    ###################################################################################
    ###################################################################################

    @property
    def events(self):
        '''
            list(Event): List of the events
        '''
        return list(self._events.values())

    def events_as_dict(self):
        return self._events

    # endregion
    ###################################################################################
    ###################################################################################
    # region Using for
    ###################################################################################
    ###################################################################################

    @property
    def using_for(self):
        return self._using_for

    def reverse_using_for(self, name):
        '''
            Returns:
            (list)
        '''
        return self._using_for[name]

    # endregion
    ###################################################################################
    ###################################################################################
    # region Variables
    ###################################################################################
    ###################################################################################

    @property
    def variables(self):
        '''
            list(StateVariable): List of the state variables. Alias to self.state_variables
        '''
        return list(self.state_variables)

    def variables_as_dict(self):
        return self._variables

    @property
    def state_variables(self):
        '''
            list(StateVariable): List of the state variables.
        '''
        return list(self._variables.values())

    @property
    def slithir_variables(self):
        '''
            List all of the slithir variables (non SSA)
        '''
        slithir_variables = [f.slithir_variables for f in self.functions + self.modifiers]
        slithir_variables = [item for sublist in slithir_variables for item in sublist]
        return list(set(slithir_variables))

    # endregion
    ###################################################################################
    ###################################################################################
    # region Constructors
    ###################################################################################
    ###################################################################################

    @property
    def constructor(self):
        '''
            Return the contract's immediate constructor.
            If there is no immediate constructor, returns the first constructor
            executed, following the c3 linearization
            Return None if there is no constructor.
        '''
        cst = self.constructor_not_inherited
        if cst:
            return cst
        for inherited_contract in self.inheritance:
            cst = inherited_contract.constructor_not_inherited
            if cst:
                return cst
        return None

    @property
    def constructor_not_inherited(self):
        return next((func for func in self.functions if func.is_constructor and func.contract == self), None)

    @property
    def constructors(self):
        '''
            Return the list of constructors (including inherited)
        '''
        return [func for func in self.functions if func.is_constructor]

    @property
    def explicit_base_constructor_calls(self):
        """
            list(Function): List of the base constructors called explicitly by this contract definition.

                            Base constructors called by any constructor definition will not be included.
                            Base constructors implicitly called by the contract definition (without
                            parenthesis) will not be included.

                            On "contract B is A(){..}" it returns the constructor of A
        """
        return [c.constructor for c in self._explicit_base_constructor_calls if c.constructor]

    # endregion
    ###################################################################################
    ###################################################################################
    # region Functions and Modifiers
    ###################################################################################
    ###################################################################################

    @property
    def functions_signatures(self):
        """
        Return the signatures of all the public/eterxnal functions/state variables
        :return: list(string) the signatures of all the functions that can be called
        """
        if self._signatures == None:
            sigs = [v.full_name for v in self.state_variables if v.visibility in ['public',
                                                                                  'external']]

            sigs += set([f.full_name for f in self.functions if f.visibility in ['public', 'external']])
            self._signatures = list(set(sigs))
        return self._signatures

    @property
    def functions(self):
        '''
            list(Function): List of the functions
        '''
        return list(self._functions.values())

    def functions_as_dict(self):
        return self._functions

    @property
    def functions_inherited(self):
        '''
            list(Function): List of the inherited functions
        '''
        return [f for f in self.functions if f.contract != self]

    @property
    def functions_not_inherited(self):
        '''
            list(Function): List of the functions defined within the contract (not inherited)
        '''
        return [f for f in self.functions if f.contract == self]

    @property
    def functions_entry_points(self):
        '''
            list(Functions): List of public and external functions
        '''
        return [f for f in self.functions if f.visibility in ['public', 'external']]

    @property
    def modifiers(self):
        '''
            list(Modifier): List of the modifiers
        '''
        return list(self._modifiers.values())

    def modifiers_as_dict(self):
        return self._modifiers

    @property
    def modifiers_inherited(self):
        '''
            list(Modifier): List of the inherited modifiers
        '''
        return [m for m in self.modifiers if m.contract != self]

    @property
    def modifiers_not_inherited(self):
        '''
            list(Modifier): List of the modifiers defined within the contract (not inherited)
        '''
        return [m for m in self.modifiers if m.contract == self]

    @property
    def functions_and_modifiers(self):
        '''
            list(Function|Modifier): List of the functions and modifiers
        '''
        return self.functions + self.modifiers

    @property
    def functions_and_modifiers_inherited(self):
        '''
            list(Function|Modifier): List of the inherited functions and modifiers
        '''
        return self.functions_inherited + self.modifiers_inherited

    @property
    def functions_and_modifiers_not_inherited(self):
        '''
            list(Function|Modifier): List of the functions and modifiers defined within the contract (not inherited)
        '''
        return self.functions_not_inherited + self.modifiers_not_inherited

    # endregion
    ###################################################################################
    ###################################################################################
    # region Inheritance
    ###################################################################################
    ###################################################################################

    @property
    def inheritance(self):
        '''
            list(Contract): Inheritance list. Order: the first elem is the first father to be executed
        '''
        return list(self._inheritance)

    @property
    def immediate_inheritance(self):
        '''
            list(Contract): List of contracts immediately inherited from (fathers). Order: order of declaration.
        '''
        return list(self._immediate_inheritance)

    @property
    def inheritance_reverse(self):
        '''
            list(Contract): Inheritance list. Order: the last elem is the first father to be executed
        '''
        return reversed(self._inheritance)

    def setInheritance(self, inheritance, immediate_inheritance, called_base_constructor_contracts):
        self._inheritance = inheritance
        self._immediate_inheritance = immediate_inheritance
        self._explicit_base_constructor_calls = called_base_constructor_contracts

    @property
    def derived_contracts(self):
        '''
            list(Contract): Return the list of contracts derived from self
        '''
        candidates = self.slither.contracts
        return [c for c in candidates if self in c.inheritance]

    # endregion
    ###################################################################################
    ###################################################################################
    # region Getters from/to object
    ###################################################################################
    ###################################################################################

    def get_functions_reading_from_variable(self, variable):
        '''
            Return the functions reading the variable
        '''
        return [f for f in self.functions if f.is_reading(variable)]

    def get_functions_writing_to_variable(self, variable):
        '''
            Return the functions writting the variable
        '''
        return [f for f in self.functions if f.is_writing(variable)]

    def get_source_var_declaration(self, var):
        """ Return the source mapping where the variable is declared

        Args:
            var (str): variable name
        Returns:
            (dict): sourceMapping
        """
        return next((x.source_mapping for x in self.variables if x.name == var))

    def get_source_event_declaration(self, event):
        """ Return the source mapping where the event is declared

        Args:
            event (str): event name
        Returns:
            (dict): sourceMapping
        """
        return next((x.source_mapping for x in self.events if x.name == event))

    def get_function_from_signature(self, function_signature):
        """
            Return a function from a signature
        Args:
            function_signature (str): signature of the function (without return statement)
        Returns:
            Function
        """
        return next((f for f in self.functions if f.full_name == function_signature), None)

    def get_modifier_from_signature(self, modifier_signature):
        """
            Return a modifier from a signature
        Args:
            modifier_name (str): signature of the modifier
        Returns:
            Modifier
        """
        return next((m for m in self.modifiers if m.full_name == modifier_signature), None)

    def get_state_variable_from_name(self, variable_name):
        """
            Return a state variable from a name
        Args:
            varible_name (str): name of the variable
        Returns:
            StateVariable
        """
        return next((v for v in self.state_variables if v.name == variable_name), None)

    def get_structure_from_name(self, structure_name):
        """
            Return a structure from a name
        Args:
            structure_name (str): name of the structure
        Returns:
            Structure
        """
        return next((st for st in self.structures if st.name == structure_name), None)

    def get_structure_from_canonical_name(self, structure_name):
        """
            Return a structure from a canonical name
        Args:
            structure_name (str): canonical name of the structure
        Returns:
            Structure
        """
        return next((st for st in self.structures if st.canonical_name == structure_name), None)

    def get_event_from_name(self, event_name):
        """
            Return an event from a name
        Args:
            event_name (str): name of the event
        Returns:
            Event
        """
        return next((e for e in self.events if e.name == event_name), None)

    def get_enum_from_name(self, enum_name):
        """
            Return an enum from a name
        Args:
            enum_name (str): name of the enum
        Returns:
            Enum
        """
        return next((e for e in self.enums if e.name == enum_name), None)

    def get_enum_from_canonical_name(self, enum_name):
        """
            Return an enum from a canonical name
        Args:
            enum_name (str): canonical name of the enum
        Returns:
            Enum
        """
        return next((e for e in self.enums if e.canonical_name == enum_name), None)

    def get_functions_overridden_by(self, function):
        '''
            Return the list of functions overriden by the function
        Args:
            (core.Function)
        Returns:
            list(core.Function)

        '''
        candidates = [c.functions_not_inherited for c in self.inheritance]
        candidates = [candidate for sublist in candidates for candidate in sublist]
        return [f for f in candidates if f.full_name == function.full_name]

    # endregion
    ###################################################################################
    ###################################################################################
    # region Recursive getters
    ###################################################################################
    ###################################################################################

    @property
    def all_functions_called(self):
        '''
            list(Function): List of functions reachable from the contract (include super)
        '''
        all_calls = [f.all_internal_calls() for f in self.functions + self.modifiers] + [self.functions + self.modifiers]
        all_calls = [item for sublist in all_calls for item in sublist] + self.functions
        all_calls = list(set(all_calls))

        all_constructors = [c.constructor for c in self.inheritance]
        all_constructors = list(set([c for c in all_constructors if c]))

        all_calls = set(all_calls+all_constructors)

        return [c for c in all_calls if isinstance(c, Function)]

    @property
    def all_state_variables_written(self):
        '''
            list(StateVariable): List all of the state variables written
        '''
        all_state_variables_written = [f.all_state_variables_written() for f in self.functions + self.modifiers]
        all_state_variables_written = [item for sublist in all_state_variables_written for item in sublist]
        return list(set(all_state_variables_written))

    @property
    def all_state_variables_read(self):
        '''
            list(StateVariable): List all of the state variables read
        '''
        all_state_variables_read = [f.all_state_variables_read() for f in self.functions + self.modifiers]
        all_state_variables_read = [item for sublist in all_state_variables_read for item in sublist]
        return list(set(all_state_variables_read))

    # endregion
    ###################################################################################
    ###################################################################################
    # region Summary information
    ###################################################################################
    ###################################################################################

    def get_summary(self):
        """ Return the function summary

        Returns:
            (str, list, list, list, list): (name, inheritance, variables, fuction summaries, modifier summaries)
        """
        func_summaries = [f.get_summary() for f in self.functions]
        modif_summaries = [f.get_summary() for f in self.modifiers]
        return (self.name, [str(x) for x in self.inheritance], [str(x) for x in self.variables], func_summaries, modif_summaries)

    def is_signature_only(self):
        """ Detect if the contract has only abstract functions

        Returns:
            bool: true if the function are abstract functions
        """
        return all((not f.is_implemented) for f in self.functions)

    # endregion
    ###################################################################################
    ###################################################################################
    # region ERC conformance
    ###################################################################################
    ###################################################################################

    def ercs(self):
        """
        Return the ERC implemented
        :return: list of string
        """
        all = [('ERC20', lambda x: x.is_erc20()),
               ('ERC165', lambda x: x.is_erc165()),
               ('ERC1820', lambda x: x.is_erc1820()),
               ('ERC223', lambda x: x.is_erc223()),
               ('ERC721', lambda x: x.is_erc721()),
               ('ERC777', lambda x: x.is_erc777())]

        return [erc[0] for erc in all if erc[1](self)]

    def is_erc20(self):
        """
            Check if the contract is an erc20 token

            Note: it does not check for correct return values
        :return: Returns a true if the contract is an erc20
        """
        full_names = self.functions_signatures
        return all((s in full_names for s in ERC20_signatures))

    def is_erc165(self):
        """
            Check if the contract is an erc165 token

            Note: it does not check for correct return values
        :return: Returns a true if the contract is an erc165
        """
        full_names = self.functions_signatures
        return all((s in full_names for s in ERC165_signatures))

    def is_erc1820(self):
        """
            Check if the contract is an erc1820

            Note: it does not check for correct return values
        :return: Returns a true if the contract is an erc165
        """
        full_names = self.functions_signatures
        return all((s in full_names for s in ERC1820_signatures))

    def is_erc223(self):
        """
            Check if the contract is an erc223 token

            Note: it does not check for correct return values
        :return: Returns a true if the contract is an erc223
        """
        full_names = self.functions_signatures
        return all((s in full_names for s in ERC223_signatures))

    def is_erc721(self):
        """
            Check if the contract is an erc721 token

            Note: it does not check for correct return values
        :return: Returns a true if the contract is an erc721
        """
        full_names = self.functions_signatures
        return all((s in full_names for s in ERC721_signatures))

    def is_erc777(self):
        """
            Check if the contract is an erc777

            Note: it does not check for correct return values
        :return: Returns a true if the contract is an erc165
        """
        full_names = self.functions_signatures
        return all((s in full_names for s in ERC777_signatures))

    def is_possible_erc20(self):
        """
        Checks if the provided contract could be attempting to implement ERC20 standards.
        :param contract: The contract to check for token compatibility.
        :return: Returns a boolean indicating if the provided contract met the token standard.
        """
        # We do not check for all the functions, as name(), symbol(), might give too many FPs
        full_names = self.functions_signatures
        return 'transfer(address,uint256)' in full_names or \
               'transferFrom(address,address,uint256)' in full_names or \
               'approve(address,uint256)' in full_names

    def is_possible_erc721(self):
        """
        Checks if the provided contract could be attempting to implement ERC721 standards.
        :param contract: The contract to check for token compatibility.
        :return: Returns a boolean indicating if the provided contract met the token standard.
        """
        # We do not check for all the functions, as name(), symbol(), might give too many FPs
        full_names = self.functions_signatures
        return ('ownerOf(uint256)' in full_names or
                'safeTransferFrom(address,address,uint256,bytes)' in full_names or
                'safeTransferFrom(address,address,uint256)' in full_names or
                'setApprovalForAll(address,bool)' in full_names or
                'getApproved(uint256)' in full_names or
                'isApprovedForAll(address,address)' in full_names)


    # endregion
    ###################################################################################
    ###################################################################################
    # region Dependencies
    ###################################################################################
    ###################################################################################

    def is_from_dependency(self):
        if self.slither.crytic_compile is None:
            return False
        return self.slither.crytic_compile.is_dependency(self.source_mapping['filename_absolute'])

    # endregion
    ###################################################################################
    ###################################################################################
    # region Function analyses
    ###################################################################################
    ###################################################################################

    def update_read_write_using_ssa(self):
        for function in self.functions + self.modifiers:
            function.update_read_write_using_ssa()

    # endregion
    ###################################################################################
    ###################################################################################
    # region Built in definitions
    ###################################################################################
    ###################################################################################

    def __eq__(self, other):
        if isinstance(other, str):
            return other == self.name
        return NotImplemented

    def __neq__(self, other):
        if isinstance(other, str):
            return other != self.name
        return NotImplemented

    def __str__(self):
        return self.name

    # endregion
