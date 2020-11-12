from preprocessor.parser import parse
from os.path import join

if __name__ == '__main__':
	with open(join('test', '__main__.py.tart')) as f:
		code = f.read()

	tree = parse(code)

	with open('out.test.txt', 'w') as f:
		f.write(str(tree))

