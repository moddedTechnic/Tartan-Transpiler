from os.path import abspath, dirname, join

class Grammar:
	def __init__(self, grammar_name, start):
		self.path = join(dirname(__file__), 'grammars', grammar_name + '.lark')
		self.start = start

	def __repr__(self):
		with open(self.path, 'r') as f:
			return f.read()
