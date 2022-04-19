import os
from chair.utils import exec_cmd

def execute(chair_path):
	exec_cmd('npm install yarn', os.path.join(chair_path, 'apps/vmraid'))
