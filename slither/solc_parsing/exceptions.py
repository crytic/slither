from slither.exceptions import SlitherException

class ParsingError(SlitherException): pass

class ParsingNameReuse(SlitherException): pass

class ParsingContractNotFound(SlitherException): pass

class VariableNotFound(SlitherException): pass
