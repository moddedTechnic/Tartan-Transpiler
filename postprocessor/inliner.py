from __future__ import generator_stop
from ast import *
from astunparse import dump

from utils import log

from .ast_manipulator import ASTManipulator


class Inliner(ASTManipulator):
	def __init__(self, *args, **kwargs) -> None:
		super().__init__(*args, **kwargs)
		
		self.pass_ = -1
		self.assignments = {}
		self.constants = {}
		self.used = set()

		self.blacklist = [
			'open'
		]

	def visit_Assign(self, node: Name) -> AST:
		node = self.generic_visit(node)

		if isinstance(node, Assign):
			if self.pass_ == 0:
				for target in node.targets:
					if isinstance(target, Name):
						if target.id in self.assignments.keys():
							self.assignments[target.id] += 1
						else:
							self.assignments[target.id] = 1

			elif self.pass_ == 1:
				if len(node.targets) == 1:
					target = node.targets[0]
					if isinstance(target, Name):
						if isinstance(target.ctx, Store):
							self.constants[target.id] = self.generic_visit(node.value)
							log(dump(node.value))

			elif self.pass_ == 4:
				targets = []
				for target in node.targets:
					if target.id in self.used:
						targets.append(target)
				node.targets = targets
				if len(targets) == 0:
					return None

		return node

	def visit_Name(self, node: Name) -> AST:
		node = self.generic_visit(node)

		if isinstance(node, Name):
			if self.pass_ == 2:
				if isinstance(node.ctx, Load):
					if node.id in self.assignments.keys() and node.id in self.constants.keys() and self.assignments[node.id] == 1:
						c = self.constants[node.id]
						if isinstance(c, Call):
							f = c.func
							if isinstance(f, Name):
								if f.id not in self.blacklist:
									c.col_offset = node.col_offset
									c.lineno = node.lineno
									return c
						elif issubclass(type(c), expr):
							c.col_offset = node.col_offset
							c.lineno = node.lineno
							return c
			
			elif self.pass_ == 3:
				if isinstance(node.ctx, Load):
					self.used.add(node.id)

		return node

	def visit_Call(self, node: Call) -> AST:
		node = self.generic_visit(node)

		if isinstance(node, Call):
			kwds = []
			for kwd in node.keywords:
				kwds.append(self.generic_visit(kwd))
			node.keywords = kwds

			args = []
			for arg in node.args:
				args.append(self.generic_visit(arg))
			node.args = args

		return node
		
	def inline(self, tree: AST):
		for i in range(5):
			self.pass_ = i
			tree = self.process(tree)
		
		return tree
