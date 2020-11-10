
class PreProcessor:
	def __init__(self, options) -> None:
		self.options = options

	def remove_comments(self, code: str) -> str:
		code = '\n'.join([ l.split('##')[0] for l in code.split('\n') ])
		
		running = True
		while running:
			symbol = ''
			start_comment = -1
			end_comment = -1

			for i, c in enumerate(str(code)):
				if c in (' ', '\n', '\r', '\t'):
					if symbol == '#{':
						start_comment = i - 2
					elif symbol == '}#':
						end_comment = i
						code = code[:start_comment] + code[end_comment:]
						break
					symbol = ''
					continue

				symbol += c

			else:
				running = False

		return code

	def region(self, code: str) -> str:
		return code

	def preprocess(self, code: str) -> str:
		code = self.remove_comments(code)
		code = self.region(code)
		return code
