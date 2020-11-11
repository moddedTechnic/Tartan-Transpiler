from logging import DEBUG

from lark import Lark, logger

from preprocessor.indenter import PythonIndenter
from preprocessor.treeify import Treeify

from .grammar import Grammar

# logger.setLevel(DEBUG)

def parse(code):
	grammar = Grammar('python', 'file_input')
	parser = Lark.open(grammar.path, rel_to=__file__, start=grammar.start, parser='lalr', postlex=PythonIndenter())
	tree = parser.parse(code + '\n')
	return Treeify().transform(tree)

