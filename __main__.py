from ast import parse

from os.path import join, dirname, exists
from os import makedirs as mkdir

from astunparse import unparse, dump

from options import Options
from generator import Generator
from optimizer import Optimizer
from auto_import import Importer
from remove_unused import UnusedRemover
from unparser import Unparser
from minifier import Minifier

from utils import log, setup


def main():
	fpath = join('test', '__main__.tart')
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

	tree = parse(data)
	tree = Generator(options=options).generate(tree)
	tree = Optimizer(options=options).optimize(tree)
	tree = Importer( options=options).clean_imports(tree)
	tree = UnusedRemover(options=options).remove_unused(tree)
	code = Unparser.unparse(tree)
	code = Minifier(options=options).minify(code)

	log(dump(tree))
	log(code.replace('\n', '\\n\n'))

	path_parts = fpath.split('.')
	out_path = join('dist',
	                ''.join(*path_parts[:-1]) + '.py')
	out_dir = dirname(out_path)

	if not exists(out_dir):
	    mkdir(out_dir)

	with open(out_path, 'w') as f:
	    f.write(code)

if __name__ == '__main__':
	setup()
	main()
