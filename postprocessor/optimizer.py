from ast import *
from astunparse import dump

from importlib import import_module

from typing import Union

from .ast_manipulator import ASTManipulator


class Optimizer(ASTManipulator):
	def __init__(self, *args, **kwargs) -> None:
		super().__init__(*args, **kwargs)
		self.asnames = []

		self.functions = {}
		self.vars = {}

	@property
	def aliases(self):
		return [ n[2] for n in self.asnames ]

	def visit_BinOp(self, node: BinOp) -> Union[BinOp, Constant]:
		node = self.generic_visit(node)

		left, right = node.left, node.right
		op = node.op

		if isinstance(left, Constant) and isinstance(right, Constant):
			if isinstance(op, Add):
				return self.constant(left.value + right.value, node)
			if isinstance(op, Sub):
				return self.constant(left.value - right.value, node)
			if isinstance(op, Mult):
				return self.constant(left.value * right.value, node)
			if isinstance(op, Div):
				return self.constant(left.value / right.value, node)
			if isinstance(op, Pow):
				return self.constant(left.value ** right.value, node)
			if isinstance(op, Mod):
				return self.constant(left.value % right.value, node)
			if isinstance(op, MatMult):
				return self.constant(left.value @ right.value, node)

			if isinstance(op, BitAnd):
				return self.constant(left.value & right.value, node)
			if isinstance(op, BitOr):
				return self.constant(left.value | right.value, node)
			if isinstance(op, BitXor):
				return self.constant(left.value ^ right.value, node)

			if isinstance(op, RShift):
				return self.constant(left.value >> right.value, node)
			if isinstance(op, LShift):
				return self.constant(left.value << right.value, node)

		return node

	def visit_UnaryOp(self, node: UnaryOp) -> Union[UnaryOp, Constant]:
		node = self.generic_visit(node)
		
		value = node.operand
		op = node.op

		if isinstance(value, Constant):
			if isinstance(op, UAdd):
				return self.constant(+value.value, node)
			if isinstance(op, USub):
				return self.constant(-value.value, node)
			if isinstance(op, Not):
				return self.constant(not value, node)

		return node

	def visit_IfExp(self, node: IfExp) -> AST:
		node = self.generic_visit(node)

		if isinstance(node.test, Constant):
			if type(node.test.value) == bool:
				self.modified = True
				if node.test.value:
					return node.body
				else:
					return node.orelse

		return node

	def visit_If(self, node: If) -> AST:
		node = self.generic_visit(node)

		if isinstance(node.test, Constant):
			if type(node.test.value) == bool:
				self.modified = True
				if node.test.value:
					return node.body
				else:
					return node.orelse

		return node

	def visit_Compare(self, node: Compare) -> AST:
		node = self.generic_visit(node)

		if isinstance(node, Compare):
			if isinstance(node.left, Constant) and isinstance(node.comparators[0], Constant):
				if isinstance(node.ops[0], Gt):
					return self.constant(node.left.value > node.comparators[0].value, node)
				if isinstance(node.ops[0], GtE):
					return self.constant(node.left.value >= node.comparators[0].value, node)
				if isinstance(node.ops[0], Lt):
					return self.constant(node.left.value < node.comparators[0].value, node)
				if isinstance(node.ops[0], LtE):
					return self.constant(node.left.value <= node.comparators[0].value, node)
				if isinstance(node.ops[0], Eq):
					return self.constant(node.left.value == node.comparators[0].value, node)
				if isinstance(node.ops[0], NotEq):
					return self.constant(node.left.value != node.comparators[0].value, node)
				if isinstance(node.ops[0], Is):
					return self.constant(node.left.value is node.comparators[0].value, node)
				if isinstance(node.ops[0], IsNot):
					return self.constant(node.left.value is not node.comparators[0].value, node)

		return node

	def visit_BoolOp(self, node: BoolOp) -> AST:
		node = self.generic_visit(node)

		if isinstance(node, BoolOp):
			if isinstance(node.op, And):
				if isinstance(node.values[0], Constant) and not node.values[0].value:
					return self.constant(False, node)
				if isinstance(node.values[1], Constant) and not node.values[1].value:
					return self.constant(False, node)
				if isinstance(node.values[0], Constant) and isinstance(node.values[1], Constant):
					return self.constant(node.values[0].value and node.values[1].value, node)

			if isinstance(node.op, Or):
				if isinstance(node.values[0], Constant) and node.values[0].value:
					return self.constant(True, node)
				if isinstance(node.values[1], Constant) and node.values[1].value:
					return self.constant(True, node)
				if isinstance(node.values[0], Constant) and isinstance(node.values[1], Constant):
					return self.constant(node.values[0].value or node.values[1].value, node)

		return node

	def visit_Return(self, node: Return) -> AST:
		node = self.generic_visit(node)

		if isinstance(node, Return):
			if isinstance(node.value, Constant):
				if node.value.value is None:
					self.modified = True
					return Return(value=None, lineno=node.lineno, col_offset=node.col_offset)

		return node

	def visit_Call(self, node: Call) -> AST:
		node = self.generic_visit(node)

		if isinstance(node, Call):
			if isinstance(node.func, Name):
				constant_args = True
				for arg in node.args:
					if not isinstance(arg, Constant):
						constant_args = False
				if constant_args:
					for module in self.options.auto_eval_mod:
						m = import_module(module)
						if node.func.id in dir(m):
							return self.constant(m.__dict__[node.func.id](*[ a.value for a in node.args ]), node)
						elif node.func.id in self.aliases:
							idx = self.aliases.index(node.func.id)
							name = self.asnames[idx][1]
							if name in dir(m):
								return self.constant(m.__dict__[name](*[ a.value for a in node.args ]), node)
			
				if node.func.id in self.functions.keys():
					body = self.functions[node.func.id]
					if len(body) == 1:
						self.modified = True
						return body[0]

		return node

	def visit_ImportFrom(self, node: ImportFrom) -> AST:
		node = self.generic_visit(node)

		if isinstance(node, ImportFrom):
			module = node.module
			names  = node.names
			to_add = [
				(
					module, n.name,
					(n.asname if n.asname is not None else n.name)
				)
				for n in names if (
					module, n.name,
					(n.asname if n.asname is not None else n.name)
				) not in self.asnames
			]
			if len(to_add) > 0:
				self.modified = True
				[ self.asnames.append(a) for a in to_add ]

		return node

	def visit_FunctionDef(self, node: FunctionDef) -> AST:
		node = self.generic_visit(node)

		if isinstance(node, FunctionDef):
			if len(node.body) > 1:
				new_body = []
				for n in node.body:
					if n is None: continue
					if isinstance(n, Expr):
						if isinstance(n.value, Expr):
							if isinstance(n.value.value, Constant):
								if n.value.value.value is None:
									continue
					new_body.append(n)

				if new_body != node.body:
					self.modified = True
					node.body = new_body
				
				end = node.body[-1]
				if isinstance(end, Return):
					if end.value is None:
						node.body.pop(-1)

		self.functions[node.name] = node.body
		return node

	def visit_With(self, node: With) -> AST:
		node = self.generic_visit(node)
		if isinstance(node, With):
			node.body = [ self.visit(b) for b in node.body ]
		return node

	def visit_Assign(self, node: Assign) -> AST:
		node = self.generic_visit(node)
		if isinstance(node, Assign):
			if len(node.targets) == 1:
				n = node.targets[0]
				if n in self.vars.keys():
					self.vars[n]['changed'] = True
				else:
					self.vars[n] = {
						'value': node.value,
						'changed': False,
					}
				self.modified = True
		return node

	def visit_AnnAssign(self, node: AnnAssign) -> AST:
		node = self.generic_visit(node)
		if isinstance(node, AnnAssign):
			n = node.target
			if n in self.vars.keys():
				self.vars[n]['changed'] = True
			else:
				self.vars[n] = {
					'changed': True,
				}
			self.modified = True
		return node

	def optimize(self, tree: AST) -> AST:
		return self.process(tree)
