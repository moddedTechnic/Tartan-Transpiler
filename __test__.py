from preprocessor.parser import parse

if __name__ == '__main__':
	tree = parse('''
node: str = 'tru'
node += 'e'
print(node, sep=', ', end='\\n\\t')
constants = {
	'true': True,
	'false': False,
	'null': None,
	'noop': None,
}

## this is a comment

for k, v in constants.items():
	if node == k:
		print(self.constant(v, node))
		break
	print(node)''')

	with open('out.test.txt', 'w') as f:
		f.write(str(tree))

