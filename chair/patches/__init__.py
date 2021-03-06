import os, importlib

def run(chair_path):
	source_patch_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'patches.txt')
	target_patch_file = os.path.join(os.path.abspath(chair_path), 'patches.txt')

	with open(source_patch_file, 'r') as f:
		patches = [p.strip() for p in f.read().splitlines()
			if p.strip() and not p.strip().startswith("#")]

	executed_patches = []
	if os.path.exists(target_patch_file):
		with open(target_patch_file, 'r') as f:
			executed_patches = f.read().splitlines()

	try:
		for patch in patches:
			if patch not in executed_patches:
				module = importlib.import_module(patch.split()[0])
				execute = getattr(module, 'execute')
				result = execute(chair_path)

				if result != False:
					executed_patches.append(patch)

	finally:
		with open(target_patch_file, 'w') as f:
			f.write('\n'.join(executed_patches))

			# end with an empty line
			f.write('\n')
