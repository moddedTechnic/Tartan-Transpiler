from io import StringIO
import sys
import ast

import six
StringIO = six.moves.StringIO
from astunparse import Unparser as _Unparser
from astunparse.unparser import interleave


# Based mostly on ASTUnparse, mainly less whitespace
class Unparser(_Unparser):
	def fill(self, text = ""):
		"Indent a piece of text, according to the current indentation level"
		self.f.write("\n"+"\t"*self._indent + text)
		
	def _NamedExpr(self, tree):
		self.write("(")
		self.dispatch(tree.target)
		self.write(":=")
		self.dispatch(tree.value)
		self.write(")")
		
	def _Import(self, t):
		self.fill('import ')
		interleave(lambda: self.write(','), self.dispatch, t.names)

	def _ImportFrom(self, t):
		# A from __future__ import may affect unparsing, so record it.
		if t.module and t.module == '__future__':
			self.future_imports.extend(n.name for n in t.names)

		self.fill('from ')
		self.write('.' * t.level)
		if t.module:
			self.write(t.module)
		self.write(' import ')
		interleave(lambda: self.write(','), self.dispatch, t.names)
		
	def _Assign(self, t):
		self.fill()
		for target in t.targets:
			self.dispatch(target)
			self.write('=')
		self.dispatch(t.value)

	def _AugAssign(self, t):
		self.fill()
		self.dispatch(t.target)
		self.write(self.binop[t.op.__class__.__name__]+"=")
		self.dispatch(t.value)

	def _AnnAssign(self, t):
		self.fill()
		if not t.simple and isinstance(t.target, ast.Name):
			self.write('(')
		self.dispatch(t.target)
		if not t.simple and isinstance(t.target, ast.Name):
			self.write(')')
		self.write(":")
		self.dispatch(t.annotation)
		if t.value:
			self.write("=")
			self.dispatch(t.value)

	def _Delete(self, t):
		self.fill("del ")
		interleave(lambda: self.write(","), self.dispatch, t.targets)

	def _Assert(self, t):
		self.fill("assert ")
		self.dispatch(t.test)
		if t.msg:
			self.write(",")
			self.dispatch(t.msg)

	def _Exec(self, t):
		self.fill("exec ")
		self.dispatch(t.body)
		if t.globals:
			self.write(" in ")
			self.dispatch(t.globals)
		if t.locals:
			self.write(",")
			self.dispatch(t.locals)

	def _Print(self, t):
		self.fill("print ")
		do_comma = False
		if t.dest:
			self.write(">>")
			self.dispatch(t.dest)
			do_comma = True
		for e in t.values:
			if do_comma:self.write(",")
			else:do_comma=True
			self.dispatch(e)
		if not t.nl:
			self.write(",")

	def _Global(self, t):
		self.fill("global ")
		interleave(lambda: self.write(","), self.write, t.names)

	def _Nonlocal(self, t):
		self.fill("nonlocal ")
		interleave(lambda: self.write(","), self.write, t.names)

	def _Raise(self, t):
		self.fill("raise")
		if six.PY3:
			if not t.exc:
				assert not t.cause
				return
			self.write(" ")
			self.dispatch(t.exc)
			if t.cause:
				self.write(" from ")
				self.dispatch(t.cause)
		else:
			self.write(" ")
			if t.type:
				self.dispatch(t.type)
			if t.inst:
				self.write(",")
				self.dispatch(t.inst)
			if t.tback:
				self.write(",")
				self.dispatch(t.tback)

	def _ClassDef(self, t):
		for deco in t.decorator_list:
			self.fill('@')
			self.dispatch(deco)
		self.fill('class '+t.name)
		if six.PY3:
			self.write('(')
			comma = False
			for e in t.bases:
				if comma: self.write(',')
				else: comma = True
				self.dispatch(e)
			for e in t.keywords:
				if comma: self.write(',')
				else: comma = True
				self.dispatch(e)
			if sys.version_info[:2] < (3, 5):
				if t.starargs:
					if comma: self.write(',')
					else: comma = True
					self.write('*')
					self.dispatch(t.starargs)
				if t.kwargs:
					if comma: self.write(',')
					else: comma = True
					self.write('**')
					self.dispatch(t.kwargs)
			self.write(')')
		elif t.bases:
				self.write('(')
				for a in t.bases:
					self.dispatch(a)
					self.write(',')
				self.write(')')
		self.enter()
		self.dispatch(t.body)
		self.leave()
		
	def __FunctionDef_helper(self, t, fill_suffix):
		for deco in t.decorator_list:
			self.fill('@')
			self.dispatch(deco)
		def_str = fill_suffix+' '+t.name + '('
		self.fill(def_str)
		self.dispatch(t.args)
		self.write(')')
		if getattr(t, 'returns', False):
			self.write('->')
			self.dispatch(t.returns)
		self.enter()
		self.dispatch(t.body)
		self.leave()

	def _generic_With(self, t, async_=False):
		self.fill("async with " if async_ else "with ")
		if hasattr(t, 'items'):
			interleave(lambda: self.write(","), self.dispatch, t.items)
		else:
			self.dispatch(t.context_expr)
			if t.optional_vars:
				self.write(" as ")
				self.dispatch(t.optional_vars)
		self.enter()
		self.dispatch(t.body)
		self.leave()

	def _fstring_FormattedValue(self, t, write):
		write("{")
		expr = StringIO()
		Unparser(t.value, expr)
		expr = expr.getvalue().rstrip("\n")
		write(expr)
		if t.conversion != -1:
			conversion = chr(t.conversion)
			assert conversion in "sra"
			write("!{conversion}".format(conversion=conversion))
		if t.format_spec:
			write(":")
			meth = getattr(self, "_fstring_" + type(t.format_spec).__name__)
			meth(t.format_spec, write)
		write("}")

	def _List(self, t):
		self.write("[")
		interleave(lambda: self.write(","), self.dispatch, t.elts)
		self.write("]")

	def _Dict(self, t):
		self.write("{")
		def write_key_value_pair(k, v):
			self.dispatch(k)
			self.write(":")
			self.dispatch(v)

		def write_item(item):
			k, v = item
			if k is None:
				# for dictionary unpacking operator in dicts {**{'y': 2}}
				# see PEP 448 for details
				self.write("**")
				self.dispatch(v)
			else:
				write_key_value_pair(k, v)
		interleave(lambda: self.write(","), write_item, zip(t.keys, t.values))
		self.write("}")

	def _Tuple(self, t):
		self.write("(")
		if len(t.elts) == 1:
			elt = t.elts[0]
			self.dispatch(elt)
			self.write(",")
		else:
			interleave(lambda: self.write(","), self.dispatch, t.elts)
		self.write(")")

	def _UnaryOp(self, t):
		self.write("(")
		op = self.unop[t.op.__class__.__name__]
		self.write(op)
		if op == 'not':
			self.write(' ')
		if six.PY2 and isinstance(t.op, ast.USub) and isinstance(t.operand, ast.Num):
			# If we're applying unary minus to a number, parenthesize the number.
			# This is necessary: -2147483648 is different from -(2147483648) on
			# a 32-bit machine (the first is an int, the second a long), and
			# -7j is different from -(7j).  (The first has real part 0.0, the second
			# has real part -0.0.)
			self.write("(")
			self.dispatch(t.operand)
			self.write(")")
		else:
			self.dispatch(t.operand)
		self.write(")")

	def _BinOp(self, t):
		self.write("(")
		self.dispatch(t.left)
		self.write(self.binop[t.op.__class__.__name__])
		self.dispatch(t.right)
		self.write(")")

	def _Compare(self, t):
		self.write("(")
		self.dispatch(t.left)
		for o, e in zip(t.ops, t.comparators):
			self.write(self.cmpops[o.__class__.__name__])
			self.dispatch(e)
		self.write(")")

	def _Call(self, t):
		self.dispatch(t.func)
		self.write("(")
		comma = False
		for e in t.args:
			if comma: self.write(",")
			else: comma = True
			self.dispatch(e)
		for e in t.keywords:
			if comma: self.write(",")
			else: comma = True
			self.dispatch(e)
		if sys.version_info[:2] < (3, 5):
			if t.starargs:
				if comma: self.write(",")
				else: comma = True
				self.write("*")
				self.dispatch(t.starargs)
			if t.kwargs:
				if comma: self.write(",")
				else: comma = True
				self.write("**")
				self.dispatch(t.kwargs)
		self.write(")")

	def _ExtSlice(self, t):
		interleave(lambda: self.write(','), self.dispatch, t.dims)

	# argument
	def _arg(self, t):
		self.write(t.arg)
		if t.annotation:
			self.write(':')
			self.dispatch(t.annotation)

	# others
	def _arguments(self, t):
		first = True
		# normal arguments
		all_args = getattr(t, 'posonlyargs', []) + t.args
		defaults = [None] * (len(all_args) - len(t.defaults)) + t.defaults
		for index, elements in enumerate(zip(all_args, defaults), 1):
			a, d = elements
			if first:first = False
			else: self.write(',')
			self.dispatch(a)
			if d:
				self.write('=')
				self.dispatch(d)
			if index == len(getattr(t, 'posonlyargs', ())):
				self.write(',/')

		# varargs, or bare '*' if no varargs but keyword-only arguments present
		if t.vararg or getattr(t, 'kwonlyargs', False):
			if first:first = False
			else: self.write(',')
			self.write('*')
			if t.vararg:
				if hasattr(t.vararg, 'arg'):
					self.write(t.vararg.arg)
					if t.vararg.annotation:
						self.write(':')
						self.dispatch(t.vararg.annotation)
				else:
					self.write(t.vararg)
					if getattr(t, 'varargannotation', None):
						self.write(':')
						self.dispatch(t.varargannotation)

		# keyword-only arguments
		if getattr(t, 'kwonlyargs', False):
			for a, d in zip(t.kwonlyargs, t.kw_defaults):
				if first:first = False
				else: self.write(',')
				self.dispatch(a),
				if d:
					self.write('=')
					self.dispatch(d)

		# kwargs
		if t.kwarg:
			if first:first = False
			else: self.write(', ')
			if hasattr(t.kwarg, 'arg'):
				self.write('**'+t.kwarg.arg)
				if t.kwarg.annotation:
					self.write(': ')
					self.dispatch(t.kwarg.annotation)
			else:
				self.write('**'+t.kwarg)
				if getattr(t, 'kwargannotation', None):
					self.write(': ')
					self.dispatch(t.kwargannotation)

	def _Lambda(self, t):
		self.write("(")
		self.write("lambda ")
		self.dispatch(t.args)
		self.write(":")
		self.dispatch(t.body)
		self.write(")")


	@staticmethod
	def unparse(tree: ast.AST):
		v = six.moves.StringIO()
		Unparser(tree, file=v)
		return v.getvalue()
