
from ast import NodeTransformer, AST, Constant, parse
from astunparse import unparse, dump


class ASTManipulator(NodeTransformer):
	MAX_ITERATIONS = 10
	
	def __init__(self, *args, **kwargs):
		super().__init__()
		self.modified = False
		self.options = kwargs['options'] if 'options' in kwargs.keys() else None

	def constant(self, value, node: AST):
		self.modified = True
		return Constant(value=value, kind=type(value), lineno=node.lineno, col_offset=node.col_offset)

	def process(self, tree: AST) -> AST:
		self.modified = True
		i = 0
		while self.modified and (i := i + 1) < self.MAX_ITERATIONS:
			self.modified = False
			tree = self.visit(tree)
		return parse(unparse(tree))
