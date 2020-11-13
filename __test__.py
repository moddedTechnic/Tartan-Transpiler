from os.path import join

from astunparse import unparse

from preprocessor.parser import parse

if __name__ == '__main__':
	with open(join('test', '__main__.py.tart')) as f:
		code = f.read()

	tree = parse(code)
	tree = unparse(tree)

	with open('out.test.txt', 'w') as f:
		f.write(str(tree))

