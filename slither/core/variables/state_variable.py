from .variable import Variable
from slither.core.children.child_contract import ChildContract
from slither.utils.type import export_nested_types_from_variable

class StateVariable(ChildContract, Variable):

    def __init__(self):
        super(StateVariable, self).__init__()
        self._node_initialization = None

    def is_declared_by(self, contract):
        """
        Check if the element is declared by the contract
        :param contract:
        :return:
        """
        return self.contract == contract


    ###################################################################################
    ###################################################################################
    # region Signature
    ###################################################################################
    ###################################################################################

    @property
    def signature(self):
        """
            Return the signature of the state variable as a function signature
            :return: (str, list(str), list(str)), as (name, list parameters type, list return values type)
        """
        return self.name, [str(x) for x in export_nested_types_from_variable(self)], self.type

    @property
    def signature_str(self):
        """
            Return the signature of the state variable as a function signature
            :return: str: func_name(type1,type2) returns(type3)
        """
        name, parameters, returnVars = self.signature
        return name+'('+','.join(parameters)+') returns('+','.join(returnVars)+')'

    # endregion
    ###################################################################################
    ###################################################################################
    # region Name
    ###################################################################################
    ###################################################################################

    @property
    def canonical_name(self):
        return '{}.{}'.format(self.contract.name, self.name)

    @property
    def full_name(self):
        """
            Return the name of the state variable as a function signaure
            str: func_name(type1,type2)
            :return: the function signature without the return values
        """
        name, parameters, _ = self.signature
        return name+'('+','.join(parameters)+')'

    # endregion
    ###################################################################################
    ###################################################################################
    # region IRs (initialization)
    ###################################################################################
    ###################################################################################

    @property
    def node_initialization(self):
        """
        Node for the state variable initalization
        :return:
        """
        return self._node_initialization

    @node_initialization.setter
    def node_initialization(self, node_initialization):
        self._node_initialization = node_initialization


    # endregion
    ###################################################################################
    ###################################################################################

