from ast import *
from astunparse import dump

from .ast_manipulator import ASTManipulator


class UnusedRemover(ASTManipulator):
	def __init__(self, *args, **kwargs) -> None:
		super().__init__(*args, **kwargs)

		self.functions = set()
		self.names = set()

		self.removal_pass = False

	def visit_Name(self, node: Name) -> AST:
		node = self.generic_visit(node)

		if isinstance(node, Name):
			if not self.removal_pass:
				self.names.add(node.id)

		return node

	def visit_FunctionDef(self, node: FunctionDef) -> AST:
		node = self.generic_visit(node)

		if isinstance(node, FunctionDef):
			if self.removal_pass:
				if node.name not in self.names:
					self.modified = True
					return None
			else:
				self.functions.add(node.name)

		return node

	def remove_unused(self, tree: AST) -> AST:
		tree = self.process(tree)
		self.removal_pass = True
		tree = self.process(tree)
		return tree
