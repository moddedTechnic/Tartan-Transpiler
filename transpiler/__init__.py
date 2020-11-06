from ast import parse

from re import findall

class Transpiler:
	def __init__(self, options) -> None:
		self.options = options

	def transpile(self, data: str) -> str:
		correct = False
		while not correct:
			try:
				parse(data)
			except SyntaxError as e:
				m = [ int(i) for i in findall(r'line (?P<lineno>\d+)', str(e)) ]
				res = []
				for i, line in enumerate(data.split('\n')):
					if i + 1 in m:
						if '{' in line:
							line = line.replace('{', ':')
						if '}' in line:
							line = line.replace('}', '')
					res.append(line)
				data = '\n'.join(res)
			else:
				correct = True
		return data
