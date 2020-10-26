
def setup():
	with open('out.txt', 'w') as f:
		f.write('')

def log(data):
	data = str(data)
	with open('out.txt', 'a') as f:
		f.write('\n\n')
		f.write(data)
