from ast import AST
from astunparse import unparse

from typing import Union


class Minifier:
	def  __init__(self, *args, **kwargs):
		self.options = kwargs['options'] if 'options' in kwargs.keys() else None
		self.modified = False

	def remove_blank_lines(self, code: str) -> str:
		new_code = '\n'.join([ l for l in code.split('\n') if l.strip() != '' ])
		if new_code != code:
			self.modified = True
		return new_code

	def spaces_to_tabs(self, code: str) -> str:
		new_code = code.replace('    ', '\t')
		if new_code != code:
			self.modified = True
		return new_code

	def process(self, code):
		code = self.remove_blank_lines(code)
		code = self.spaces_to_tabs(code)
		return code

	def minify(self, code: Union[AST, str]):
		if isinstance(code, AST):
			code = unparse(code)

		self.modified = True
		while self.modified:
			self.modified = False
			code = self.process(code)
		return code
