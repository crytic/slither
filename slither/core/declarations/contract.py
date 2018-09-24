""""
    Contract module
"""
import logging
from slither.core.children.child_slither import ChildSlither
from slither.core.source_mapping.source_mapping import SourceMapping
from slither.core.declarations.function import Function

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
        self._inheritance = []

        self._enums = {}
        self._structures = {}
        self._events = {}
        self._variables = {}
        self._modifiers = {}
        self._functions = {}
        self._using_for = {}
        self._kind = None


    def __eq__(self, other):
        if isinstance(other, str):
            return other == self.name
        return NotImplemented

    def __neq__(self, other):
        if isinstance(other, str):
            return other != self.name
        return NotImplemented

    @property
    def name(self):
        """str: Name of the contract."""
        return self._name

    @property
    def id(self):
        """Unique id."""
        return self._id

    @property
    def inheritance(self):
        '''
            list(Contract): Inheritance list. Order: the first elem is the first father to be executed
        '''
        return list(self._inheritance)

    @property
    def inheritance_reverse(self):
        '''
            list(Contract): Inheritance list. Order: the last elem is the first father to be executed
        '''
        return reversed(self._inheritance)

    def setInheritance(self, inheritance):
        self._inheritance = inheritance

    @property
    def structures(self):
        '''
            list(Structure): List of the structures
        '''
        return list(self._structures.values())

    def structures_as_dict(self):
        return self._structures

    @property
    def enums(self):
        return list(self._enums.values())

    def enums_as_dict(self):
        return self._enums

    @property
    def modifiers(self):
        '''
            list(Modifier): List of the modifiers
        '''
        return list(self._modifiers.values())

    def modifiers_as_dict(self):
        return self._modifiers

    @property
    def functions(self):
        '''
            list(Function): List of the functions
        '''
        return list(self._functions.values())

    @property
    def functions_inherited(self):
        '''
            list(Function): List of the inherited functions
        '''
        return [f for f in self.functions if f.contract != self]

    @property
    def functions_all_called(self):
        '''
            list(Function): List of functions reachable from the contract (include super)
        '''
        all_calls = (f.all_internal_calls() for f in self.functions)
        all_calls = [item for sublist in all_calls for item in sublist] + self.functions
        all_calls = set(all_calls)
        return [c for c in all_calls if isinstance(c, Function)]

    def functions_as_dict(self):
        return self._functions

    @property
    def events(self):
        '''
            list(Event): List of the events
        '''
        return list(self._events.values())

    def events_as_dict(self):
        return self._events

    @property
    def state_variables(self):
        '''
            list(StateVariable): List of the state variables.
        '''
        return list(self._variables.values())

    @property
    def variables(self):
        '''
            list(StateVariable): List of the state variables. Alias to self.state_variables
        '''
        return list(self.state_variables)

    def variables_as_dict(self):
        return self._variables

    @property
    def using_for(self):
        return self._using_for

    def reverse_using_for(self, name):
        return self._using_for[name]

    @property
    def contract_kind(self):
        return self._kind

    def __str__(self):
        return self.name

    def get_functions_reading_variable(self, variable):
        '''
            Return the functions reading the variable
        '''
        return [f for f in self.functions if f.is_reading(variable)]

    def get_functions_writing_variable(self, variable):
        '''
            Return the functions writting the variable
        '''
        return [f for f in self.functions if f.is_writing(variable)]

    def is_signature_only(self):
        """ Detect if the contracts is only an interface

        Returns:
            bool: true if the contract do no read or write
        """
        for f in self.functions:
            if f.variables_read_or_written:
                return False
        return True

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

    def is_erc20(self):
        """
            Check if the contract is a erc20 token
            Note: it does not check for correct return values
        Returns:
            bool
        """
        full_names = [f.full_name for f in self.functions]
        return 'transfer(address,uint256)' in full_names and\
               'transferFrom(address,address,uint256)' in full_names and\
               'approve(address,uint256)' in full_names

    def get_summary(self):
        """ Return the function summary

        Returns:
            (str, list, list, list, list): (name, inheritance, variables, fuction summaries, modifier summaries)
        """
        func_summaries = [f.get_summary() for f in self.functions]
        modif_summaries = [f.get_summary() for f in self.modifiers]
        return (self.name, [str(x) for x in self.inheritance], [str(x) for x in self.variables], func_summaries, modif_summaries)
