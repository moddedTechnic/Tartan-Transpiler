from ast import (Add, AnnAssign, Assign, AugAssign, BitAnd, BitOr, BitXor,
                 Compare, Constant, Dict, Div, FloorDiv, MatMult, Mod, Mult,
                 Pow, Sub, Lt, LtE, Gt, GtE, Eq, NotEq, LShift, RShift)
from typing import Any, List, Union

from lark import Transformer
from lark.lexer import Token
from lark.tree import Tree


class Treeify(Transformer):
	DICT_OR_SET_MAKER = 'dictorsetmaker'

	@staticmethod
	def Constant(value: Any, node: Union[Token, None] = None) -> Constant:
		if node is None:
			return Constant(value=value)
		return Constant(value=value, lineno=node.line, col_offset=node.column)

	def const_true(self, _):
		return self.Constant(True)

	def const_false(self, _):
		return self.Constant(False)

	def const_none(self, _):
		return self.Constant(None)

	def string(self, s: List[Token]):
		s = s[0]
		return self.Constant(s.value, s)

	def dict(self, d: List[Tree]):
		d = d[0]
		if d.data == self.DICT_OR_SET_MAKER:
			kv_pairs = []
			data = d.children
			for i in range(len(data) - 1):
				kv_pairs.append((data[i], data[i+1]))
			keys = [ k for k, _ in kv_pairs ]
			values = [ v for _, v in kv_pairs ]
			return Dict(keys, values)
		return

	def expr_stmt(self, s: List[Tree]):
		name = s[0]
		augment: Union[None, Tree]
		if len(s) == 2:
			augment = None
			value = s[1]
		else:
			augment, value = s[1:]

		annotation: Union[None, Tree] = None
		if isinstance(value, Tree):
			if value.data == 'annassign':
				annotation = value.children[0]
				value = value.children[1]

		if augment is not None:
			func: Union[None, Add, Sub, Mult, MatMult, Div, FloorDiv, Mod, Pow, BitAnd, BitOr, BitXor] = None
			aug: Token = augment.children[0]

			func = {
				'+=': Add,
				'-=': Sub,
				'*=': Mult,
				'@=': MatMult,
				'/=': Div,
				'//=': FloorDiv,
				'%=': Mod,
				'**=': Pow,
				'&=': BitAnd,
				'|=': BitOr,
				'^=': BitXor,
				'<<=': LShift,
				'>>=': RShift,
			}.get(aug.value, None)

			if func is not None:
				return AugAssign(
					name,
					func(),
					value
				)

		if annotation is not None:
			return AnnAssign(
				targets=[name],
				value=value,
				simple=1,
				annotation=annotation
			)

		return Assign(
			targets=[name],
			value=value
		)

	def comparison(self, c):
		x: Tree
		y: Tree
		check: Token
		x, check, y = c
		
		func = {
			'==': Eq,
			'!=': NotEq,
			'<': Lt,
			'<=': LtE,
			'>': Gt,
			'>=': GtE,
		}.get(check.value, None)

		if func is not None:
			return Compare(
				left=x,
				ops=[func()],
				comparators=[y]
			)

		else:
			raise TypeError(f'Unrecognised comparison operator: {check.value}')
