from ast import parse
from os import getcwd, makedirs as mkdir
from os.path import abspath, dirname, exists, join
from sys import argv

from astunparse import dump

from postprocessor import *
from utils import log, setup
from utils.options import Options
from utils.unparser import Unparser
from transpiler import Transpiler
from preprocessor import PreProcessor


def main():
	fpath = argv[1]
	with open(fpath, 'r') as f:
		data = f.read()
	
	auto_process_libs = [
		'math',
		'os.path',
	]

	auto_import_libs = [
		*auto_process_libs,
		'os',
	]

	options = Options(
		debug=True,
		imports=auto_import_libs,
		eval_mod=auto_process_libs,
	)

	data = PreProcessor(options=options).preprocess(data)
	data = Transpiler(options=options).transpile(data)
	tree = parse(data)
	tree = Generator(options=options).generate(tree)
	tree = Optimizer(options=options).optimize(tree)
	tree = Inliner(options=options).inline(tree)
	tree = Importer( options=options).clean_imports(tree)
	tree = UnusedRemover(options=options).remove_unused(tree)
	code = Unparser.unparse(tree)
	code = Minifier(options=options).minify(code)

	log(dump(tree))
	log(code.replace('\n', '\\n\n'))

	path_parts = fpath.split('.')
	out_path = join(getcwd(), 'dist',
					''.join(path_parts[:-1])[1:] + '.py')
	out_dir = dirname(out_path)

	if not exists(out_dir):
		mkdir(out_dir)

	with open(out_path, 'w') as f:
		f.write(code)

if __name__ == '__main__':
	setup()
	main()
