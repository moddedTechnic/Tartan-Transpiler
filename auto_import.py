from ast import *

from importlib import import_module

from typing import (
	List as List_,	Tuple as Tuple_,
)


from ast_manipulator import ASTManipulator


class Importer(ASTManipulator):
	def __init__(self, *args, **kwargs) -> None:
		super().__init__(*args, **kwargs)
		self.names: set[str] = set()
		self.functions = set()
		
		self.auto_imports = {}
		for i in self.options.auto_imports:
			self.auto_imports[i] = False

		self.imported: List_[Tuple_[str, str, str]] = []
		self.unneeded_imports = []

		self.blacklist = {
			'os': [
				'open',
			],
		}

	@property
	def aliases(self):
		return [ a[2] for a in self.imported ]

	@property
	def imported_names(self):
		return [ a[1] for a in self.imported ]

	def visit_Module(self, node: Module) -> AST:
		node = self.generic_visit(node)

		self.unneeded_imports = [
			( module, name, asname )
			for module, name, asname in self.imported
			if name not in self.names and asname not in self.names
		]

		if isinstance(node, Module):
			for module, imported in self.auto_imports.items():
				if not imported:
					names = [
						n for n in self.names
						if n in dir(import_module(module))
							and '__' not in n 
							and n not in self.functions
							and (
								n not in self.blacklist[module]
								if module in self.blacklist.keys()
								else True
							)
							and n not in self.aliases
							and n not in self.imported_names
					]

					if len(names) > 0:
						res = f'from {module} import ('
						for n in names:
							res += f'\n\t{n},'
						res += '\n)'

						res = parse(res)
						node.body.insert(0, res)

						self.modified = True
						self.auto_imports[module] = True

		return node

	def visit_Name(self, node: Name) -> AST:
		node = self.generic_visit(node)
		if isinstance(node, Name):
			self.names.add(node.id)
		return node

	def visit_ImportFrom(self, node: ImportFrom) -> AST:
		node = self.generic_visit(node)

		if isinstance(node, ImportFrom):
			[
				self.imported.append((node.module, name.name, name.asname))
				for name in node.names
			]

			names = node.names.copy()
			for name in node.names:
				for m, n, asn in self.unneeded_imports:
					if m == node.module and n == name.name:
						i = -1
						for a in names:
							i += 1
							if n == a.name:
								break
						if i >= 0:
							names.pop(i)
						break
			node.names = names

			if len(node.names) == 0:
				return

		return node

	def visit_FunctionDef(self, node: FunctionDef) -> AST:
		node = self.generic_visit(node)
		
		if isinstance(node, FunctionDef):
			self.functions.add(node.name)
		
		return node

	def clean_imports(self, tree: AST) -> AST:
		tree = self.process(tree)
		self.imported = []
		return self.process(tree)
