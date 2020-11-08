
class PreProcessor:
	def __init__(self, options) -> None:
		self.options = options

	def remove_comments(self, code: str) -> str:
		return '\n'.join([ l.split('##')[0] for l in code.split('\n') ])

	def preprocess(self, code: str) -> str:
		code = self.remove_comments(code)
		return code
