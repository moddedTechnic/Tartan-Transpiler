from ast import (Add, AnnAssign, Assign, Attribute, AugAssign, BitAnd, BitOr,
                 BitXor, Call, Compare, Constant, Dict, Div, Eq, FloorDiv, For,
                 Gt, GtE, IfExp, Load, LShift, Lt, LtE, MatMult, Mod, Module,
                 Mult, Name, NotEq, Pow, RShift, Store, Sub, keyword)
from typing import Any, List, Union

from astunparse import dump
from lark import Transformer
from lark.lexer import Token
from lark.tree import Tree

for elem in (Add, AnnAssign, Assign, AugAssign, BitAnd, BitOr, BitXor,
                 Call, Compare, Constant, Dict, Div, Eq, FloorDiv, Gt, GtE,
                 Load, LShift, Lt, LtE, MatMult, Mod, Mult, Name, NotEq, Pow,
                 RShift, Store, Sub, keyword, IfExp, For, Module, Attribute):
	setattr(elem, '__str__', lambda self: dump(self))
	setattr(elem, '__repr__', lambda self: str(self))


class Treeify(Transformer):
	DICT_OR_SET_MAKER = 'dictorsetmaker'

	@staticmethod
	def Constant(value: Any, node: Union[Token, None] = None) -> Constant:
		if node is None:
			return Constant(value=value)
		return Constant(value=value, lineno=node.line, col_offset=node.column)

	@staticmethod
	def LoadName(id: str):
		return Name(id=id, ctx=Load())

	@staticmethod
	def StoreName(id: str):
		return Name(id=id, ctx=Store())

	def const_true(self, _):
		return self.Constant(True)

	def const_false(self, _):
		return self.Constant(False)

	def const_none(self, _):
		return self.Constant(None)

	def string(self, s: List[Token]):
		s = s[0]
		return self.Constant(s.value[1:-1], s)

	def dict(self, d: List[Tree]):
		d = d[0]
		if d.data == self.DICT_OR_SET_MAKER:
			kv_pairs = []
			data = d.children
			for i in range(0, len(data) - 1, 2):
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

		temp = []
		for n in name:
			if isinstance(n, Name):
				n = self.StoreName(id=n.id)
			temp.append(n)
		name = temp.copy()

		if annotation is not None or augment is not None:
			if isinstance(name, list):
				name = name[0]

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
			if isinstance(annotation, list):
				annotation = annotation[0]
			if isinstance(annotation, Name):
				annotation = self.LoadName(annotation.id)
			return AnnAssign(
				target=name,
				value=value,
				simple=1,
				annotation=annotation
			)

		return Assign(
			targets=name,
			value=value
		)

	def comparison(self, c):
		x: Union[Tree, Name]
		y: Union[Tree, Name]
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

		if isinstance(x, list):
			x = x[0]

		if isinstance(x, Tree):
			if x.data == 'var':
				x = x.children[0]

		if isinstance(y, list):
			temp = []
			for i in y:
				if isinstance(i, Tree):
					if i.data == 'var':
						i = i.children[0]
				if isinstance(i, Name):
					i = self.LoadName(i.id)
				temp.append(i)
			y = temp
		if isinstance(y, Tree):
			if y.data == 'var':
				y = y.children[0]

		if isinstance(x, Name):
			x = self.LoadName(x.id)
		if isinstance(y, Name):
			y = self.LoadName(y.id)

		if func is not None:
			return Compare(
				left=x,
				ops=[func()],
				comparators=y
			)

		else:
			raise TypeError(f'Unrecognised comparison operator: {check.value}')

	def funccall(self, f: List[Tree]):
		func = f[0]
		args = None
		if len(f) > 1: args = f[1]

		if args is not None:
			arguments = args.children
			
			args_ = []
			kwargs = []
			
			for arg in arguments:
				if isinstance(arg, Tree):
					if arg.data == 'var':
						args_.append(arg.children[0])
					elif arg.data == 'argvalue':
						name, value = arg.children
						if isinstance(name, Tree):
							name = name.children
						if isinstance(name, list):
							name = name[0]
						kwargs.append((name, value))

			temp = []
			for kwarg in kwargs:
				name, value = kwarg
				if isinstance(name, Token):
					name = name.value
				elif isinstance(name, Name):
					name = name.id
				temp.append(keyword(arg=name, value=value))
			kwargs = temp.copy()

		else:
			args_ = []
			kwargs = []

		if isinstance(func, list):
			func = func[0]

		return Call(
			func=func,
			args=args_,
			keywords=kwargs
		)

	def NAME(self, n: Token):
		return Name(n.value)

	def var(self, v):
		if isinstance(v, Tree):
			return v.children[0]
		return v

	def compound_stmt(self, c):
		return c[0]

	def if_stmt(self, i):
		check, block = i
		return IfExp(
			test=check,
			body=block,
			orelse=None
		)

	def suite(self, s):
		return s

	def testlist(self, t):
		return t[0]

	def exprlist(self, e):
		temp = []
		for i in e:
			if isinstance(i, list):
				if len(i) == 1:
					i = i[0]
			temp.append(i)
		return temp

	def for_stmt(self, f):
		vars_, check, body = f
		return For(
			target=vars_,
			iter=check,
			body=body
		)

	def file_input(self, f):
		return Module(body=f)

	def getattr(self, g):
		# get b from a
		a, b = g
		if isinstance(a, list):
			a = a[0]
		
		if isinstance(a, Name):
			a = self.LoadName(a.id)
		if isinstance(b, Name):
			b = self.LoadName(b.id)
		
		return Attribute(
			value=a,
			attr=b
		)
