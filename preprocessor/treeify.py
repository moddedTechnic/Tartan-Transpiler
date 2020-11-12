from ast import (Add, AnnAssign, Assign, Attribute, AugAssign, BinOp, BitAnd,
                 BitOr, BitXor, Call, Compare, Constant, Dict, Div, Eq,
                 FloorDiv, For, FunctionDef, Gt, GtE, IfExp, ImportFrom, Load,
                 LShift, Lt, LtE, MatMult, Mod, Module, Mult, Name, Not, NotEq,
                 Pow, RShift, Store, Sub, UnaryOp, With, alias, keyword,
                 withitem)
from typing import Any, List, Union

from astunparse import dump
from lark import Transformer
from lark.lexer import Token
from lark.tree import Tree

for elem in (Add, AnnAssign, Assign, Attribute, AugAssign, BitAnd, BitOr,
			 BitXor, Call, Compare, Constant, Dict, Div, Eq, FloorDiv, For,
			 FunctionDef, Gt, GtE, IfExp, Load, LShift, Lt, LtE, MatMult,
			 Mod, Module, Mult, Name, NotEq, Pow, RShift, Store, Sub,
			 keyword, With, withitem, UnaryOp, Not, BinOp, alias, ImportFrom):
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
						continue
					elif arg.data == 'argvalue':
						name, value = arg.children
						if isinstance(name, Tree):
							name = name.children
						if isinstance(name, list):
							name = name[0]
						kwargs.append((name, value))
						continue
				args_.append(arg)

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

		if isinstance(func, Attribute) and isinstance(args, Tree):
			print(args.children)

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

	def funcdef(self, f):
		name, body, *_ = f
		if isinstance(name, Name):
			name = name.id
		return FunctionDef(name=name, args=[], body=body, decorator_list=[])

	def with_stmt(self, w):
		with_item, body = w
		with_item, vars_ = with_item.children
		with_item = withitem(with_item, vars_)
		items = [with_item]
		return With(items=items, body=body)

	def number(self, n):
		n: Token = n[0]
		value = {
			'DEC_NUMBER': lambda x: int(x),
			'HEX_NUMBER': lambda x: int(x, 16),
			'OCT_NUMBER': lambda x: int(x, 8),
			'BIN_NUMBER': lambda x: int(x, 2),
			'FLOAT_NUMBER': lambda x: float(x),
			'IMAG_NUMBER': lambda x: x,
		}.get(n.type, lambda x: x)(n.value)
		return self.Constant(value)

	def not_expr(self, n):
		return UnaryOp(Not(), n[0])

	def arith_expr(self, a):
		a, op, b = a
		
		op = {
			'+': Add(),
			'-': Sub(),
			'*': Mult(),
			'@': MatMult(),
			'/': Div(),
			'//': FloorDiv(),
			'%': Mod(),
			'&': BitAnd(),
			'|': BitOr(),
			'^': BitXor(),
			'<<': LShift(),
			'>>': RShift(),
		}.get(op, None)

		return BinOp(left=a, op=op, right=b)

	def import_from(self, i):
		if len(i) == 1:
			module = i[0]
			names = None
		else:
			module, names = i

		if isinstance(module, Tree):
			module = module.children
			module = '.'.join([ m.id for m in module ])

		if names is not None:
			if isinstance(names, Tree):
				names = names.children
			if isinstance(names, list):
				temp = []
				for name in names:
					if isinstance(name, Tree):
						base = name.children[0]
						if isinstance(base, Name):
							base = base.id

						if len(name.children) > 1:
							asname = name.children[1]
							if isinstance(asname, Name):
								asname = asname.id
						else:
							asname = None
						name = alias(name=base, asname=asname)
					temp.append(name)
				names = temp.copy()

		return ImportFrom(module=module, names=names)

	def import_stmt(self, i):
		if len(i) == 1:
			if isinstance(i[0], ImportFrom):
				return i[0]
		return Tree(data='import_stmt', children=i)
