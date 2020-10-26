from ast import *

from math import pi, e, inf

from ast_manipulator import ASTManipulator


class Generator(ASTManipulator):
	def __init__(self, *args, **kwargs) -> None:
		super().__init__(*args, **kwargs)
		self.main  = [ False, False ]
		self.setup = [ False, False, False ]
		self.loop  = [ False, False ]

		self.funtions = set()
		self.names = set()

	def visit_Module(self, node: Module) -> AST:
		self.generic_visit(node)

		if 'debug' in self.names and 'debug' not in self.funtions:
			node.body.insert(0, parse('''
def debug(*args, **kwargs):
	print(*args, **kwargs) if DEBUG else NOOP
'''))
			self.modified = True

		res = 'if __name__ == "__main__":'

		if not self.setup[1] and self.setup[0]:
			if self.setup[2]:
				res += '\n\tfrom sys import argv'
				res += '\n\tsetup(argv)'
			else:
				res += '\n\tsetup()'
			self.setup[1] = True

		if not self.main[1] and self.main[0]:
			res += '\n\tmain()'
			self.main[1] = True

		if not self.loop[1] and self.loop[0]:
			res += '\n\twhile True:'
			res += '\n\t\tloop()'
			self.loop[1] = True
			
		if res != 'if __name__ == "__main__":':
			self.modified = True
			node.body.append(parse(res))

		return node

	def visit_Name(self, node: Name) -> AST:
		self.generic_visit(node)

		constants = {
			'true': True,
			'false': False,
			'null': None,
			'NOOP': None,

			'QUARTER_PI': pi / 4,
			'HALF_PI': pi / 2,
			'PI': pi,
			'TAU': 2 * pi,
			'TWO_PI': 2 * pi,

			'E': e,

			'INFINITY': inf,

			'GOOGOL': 1e100,

			'DEBUG': False
		}

		for k, v in constants.items():
			if node.id == k:
				return self.constant(v, node)

		self.names.add(node.id)

		return node

	def visit_FunctionDef(self, node: FunctionDef) -> AST:
		self.generic_visit(node)

		if node.name == 'setup':
			self.setup[0] = True
			if len(node.args.args) > 0: # wants argv
				self.setup[2] = True
		if node.name == 'main':
			self.main[0] = True
		if node.name == 'loop':
			self.loop[0] = True

		self.funtions.add(node.name)

		return node

	def visit_ImportFrom(self, node: ImportFrom) -> AST:
		node = self.generic_visit(node)

		if isinstance(node, ImportFrom):
			for a in node.names:
				name = a.asname if a.asname is not None else a.name
				if name == 'setup':
					self.setup[0] = True
				if name == 'main':
					self.main[0] = True
				if name == 'loop':
					self.loop = True

		return node

	def generate(self, tree: AST):
		return self.process(tree)
