import logging
import os

from slither import Slither
from slither.core.declarations import Structure, Enum, SolidityVariableComposed, SolidityVariable, Function
from slither.core.solidity_types import ElementaryType, ArrayType, MappingType, UserDefinedType
from slither.core.variables.local_variable import LocalVariable
from slither.core.variables.local_variable_init_from_tuple import LocalVariableInitFromTuple
from slither.core.variables.state_variable import StateVariable
from slither.slithir.operations import Assignment, Index, Member, Length, Balance, Binary, \
    Unary, Condition, NewArray, NewStructure, NewContract, NewElementaryType, \
    SolidityCall, Push, Delete, EventCall, LibraryCall, InternalDynamicCall, \
    HighLevelCall, LowLevelCall, TypeConversion, Return, Transfer, Send, Unpack, InitArray, InternalCall
from slither.slithir.variables import TemporaryVariable, TupleVariable, Constant, ReferenceVariable
from .cache import load_cache

simil_logger = logging.getLogger("Slither-simil")
compiler_logger = logging.getLogger("CryticCompile")
compiler_logger.setLevel(logging.CRITICAL)
slither_logger = logging.getLogger("Slither")
slither_logger.setLevel(logging.CRITICAL)

def parse_target(target):
    if target is None:
        return None, None

    parts = target.split('.')
    if len(parts) == 1:
        return None, parts[0]
    elif len(parts) == 2:
        return parts
    else:
        simil_logger.error("Invalid target. It should be 'function' or 'Contract.function'")

def load_and_encode(infile, vmodel, ext=None, nsamples=None, **kwargs):
    r = dict()
    if infile.endswith(".npz"):
        r = load_cache(infile, nsamples=nsamples)
    else: 
        contracts = load_contracts(infile, ext=ext, nsamples=nsamples)
        for contract in contracts:
            for x,ir in encode_contract(contract, **kwargs).items():
                if ir != []:
                    y = " ".join(ir)
                    r[x] = vmodel.get_sentence_vector(y)

    return r

def load_contracts(dirname, ext=None, nsamples=None, **kwargs):
    r = []
    walk = list(os.walk(dirname))
    for x, y, files in walk:
        for f in files: 
            if ext is None or f.endswith(ext):
                r.append(x + "/".join(y) + "/" + f)

    if nsamples is None:
        return r
    else:
        # TODO: shuffle
        return r[:nsamples]

def ntype(_type):
    if isinstance(_type, ElementaryType):
        _type = str(_type)
    elif isinstance(_type, ArrayType):
        if isinstance(_type.type, ElementaryType):
            _type = str(_type)
        else:
            _type = "user_defined_array"
    elif isinstance(_type, Structure):
        _type = str(_type)
    elif isinstance(_type, Enum):
        _type = str(_type)
    elif isinstance(_type, MappingType):
        _type = str(_type)
    elif isinstance(_type, UserDefinedType):
        _type = "user_defined_type"  # TODO: this could be Contract, Enum or Struct
    else:
        _type = str(_type)

    _type = _type.replace(" memory","")
    _type = _type.replace(" storage ref","")

    if "struct" in _type:
        return "struct"
    elif "enum" in _type:
        return "enum"
    elif "tuple" in _type:
        return "tuple"
    elif "contract" in _type:
        return "contract"
    elif "mapping" in _type:
        return "mapping"
    else:
        return _type.replace(" ","_")

def encode_ir(ir):
    # operations
    if isinstance(ir, Assignment):
        return '({}):=({})'.format(encode_ir(ir.lvalue), encode_ir(ir.rvalue))
    if isinstance(ir, Index):
        return 'index({})'.format(ntype(ir._type)) 
    if isinstance(ir, Member):
        return 'member' #.format(ntype(ir._type))
    if isinstance(ir, Length):
        return 'length'
    if isinstance(ir, Balance):
        return 'balance'
    if isinstance(ir, Binary):
        return 'binary({})'.format(ir.type_str)
    if isinstance(ir, Unary):
        return 'unary({})'.format(ir.type_str) 
    if isinstance(ir, Condition):
        return 'condition({})'.format(encode_ir(ir.value))
    if isinstance(ir, NewStructure):
        return 'new_structure'
    if isinstance(ir, NewContract):
        return 'new_contract'
    if isinstance(ir, NewArray):
        return 'new_array({})'.format(ntype(ir._array_type)) 
    if isinstance(ir, NewElementaryType):
        return 'new_elementary({})'.format(ntype(ir._type)) 
    if isinstance(ir, Push):
        return 'push({},{})'.format(encode_ir(ir.value), encode_ir(ir.lvalue))
    if isinstance(ir, Delete):
        return 'delete({},{})'.format(encode_ir(ir.lvalue), encode_ir(ir.variable))
    if isinstance(ir, SolidityCall):
        return 'solidity_call({})'.format(ir.function.full_name)
    if isinstance(ir, InternalCall):
        return 'internal_call({})'.format(ntype(ir._type_call)) 
    if isinstance(ir, EventCall): # is this useful?
        return 'event'
    if isinstance(ir, LibraryCall):
        return 'library_call'
    if isinstance(ir, InternalDynamicCall):
        return 'internal_dynamic_call'
    if isinstance(ir, HighLevelCall): # TODO: improve
        return 'high_level_call'
    if isinstance(ir, LowLevelCall): # TODO: improve
        return 'low_level_call'
    if isinstance(ir, TypeConversion):
        return 'type_conversion({})'.format(ntype(ir.type))
    if isinstance(ir, Return): # this can be improved using values
        return 'return' #.format(ntype(ir.type))
    if isinstance(ir, Transfer):
        return 'transfer({})'.format(encode_ir(ir.call_value))
    if isinstance(ir, Send):
        return 'send({})'.format(encode_ir(ir.call_value))
    if isinstance(ir, Unpack): # TODO: improve
        return 'unpack'
    if isinstance(ir, InitArray): # TODO: improve
        return 'init_array'
    if isinstance(ir, Function): # TODO: investigate this
        return 'function_solc'

    # variables
    if isinstance(ir, Constant):
        return 'constant({})'.format(ntype(ir._type))
    if isinstance(ir, SolidityVariableComposed):
        return 'solidity_variable_composed({})'.format(ir.name)
    if isinstance(ir, SolidityVariable):
        return 'solidity_variable{}'.format(ir.name)
    if isinstance(ir, TemporaryVariable):
        return 'temporary_variable'
    if isinstance(ir, ReferenceVariable):
        return 'reference({})'.format(ntype(ir._type)) 
    if isinstance(ir, LocalVariable):
        return 'local_solc_variable({})'.format(ir._location) 
    if isinstance(ir, StateVariable):
        return 'state_solc_variable({})'.format(ntype(ir._type))
    if isinstance(ir, LocalVariableInitFromTuple):
        return 'local_variable_init_tuple'
    if isinstance(ir, TupleVariable):
        return 'tuple_variable'

    # default
    else:
        simil_logger.error(type(ir),"is missing encoding!")
        return ''
 
def encode_contract(cfilename, **kwargs):
    r = dict()

    # Init slither
    try:
        slither = Slither(cfilename, **kwargs)
    except:
        simil_logger.error("Compilation failed for %s using %s", cfilename, kwargs['solc'])
        return r

    # Iterate over all the contracts
    for contract in slither.contracts:

        # Iterate over all the functions
        for function in contract.functions_not_inherited:

            if function.nodes == []:
                continue

            x = (cfilename,contract.name,function.name)

            r[x] = []

            # Iterate over the nodes of the function
            for node in function.nodes:
                # Print the Solidity expression of the nodes
                # And the SlithIR operations
                if node.expression:
                    for ir in node.irs:
                        r[x].append(encode_ir(ir))
    return r


