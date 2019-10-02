"""
    Module printing summary of the contract
"""
from slither.printers.abstract_printer import AbstractPrinter



class ConstructorPrinter(AbstractPrinter):
	WIKI = 'https://github.com/crytic/slither/wiki/Printer-documentation#constructor-calls'
	ARGUMENT = 'constructor-calls'	
	HELP = 'Print the constructors executed'
	
	def _get_soruce_code(self,cst):
		src_mapping = cst.source_mapping	
		content= self.slither.source_code[src_mapping['filename_absolute']]
		start = src_mapping['start']
		end = src_mapping['start'] + src_mapping['length']
		initial_space = src_mapping['starting_column']
		return ' ' * initial_space + content[start:end]

	def output(self,_filename):
		for contract in self.contracts:
			stack_name = []
			stack_definition = []
			print("\n\nContact Name:",contract.name)
			print("	Constructor Call Sequence: ", sep=' ', end='', flush=True)
			cst = contract.constructors_declared
			if cst:
				stack_name.append(contract.name)
				stack_definition.append(self._get_soruce_code(cst))
			for inherited_contract in contract.inheritance:
				cst = inherited_contract.constructors_declared
				if cst:
					stack_name.append(inherited_contract.name)
					stack_definition.append(self._get_soruce_code(cst))
			if len(stack_name)>0:
				print(" ",stack_name[len(stack_name)-1], sep=' ', end='', flush=True)
				count = len(stack_name)-2;
				while count>=0:
					print("-->",stack_name[count], sep=' ', end='', flush=True)
					count= count-1;
				print("\n Constructor Definitions:")
				count = len(stack_definition)-1
				while count>=0:
					print("\n Contract name:", stack_name[count])
					print ("\n", stack_definition[count])
					count = count-1;
