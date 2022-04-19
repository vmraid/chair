import click, os
from chair.config.procfile import setup_procfile
from chair.config.supervisor import generate_supervisor_config
from chair.utils.app import get_current_vmraid_version, get_current_branch

def execute(chair_path):
	vmraid_branch = get_current_branch('vmraid', chair_path)
	vmraid_version = get_current_vmraid_version(chair_path)

	if not (vmraid_branch=='develop' or vmraid_version >= 7):
		# not version 7+
		# prevent running this patch
		return False

	click.confirm('\nThis update will remove Celery config and prepare the chair to use Python RQ.\n'
		'And it will overwrite Procfile and supervisor.conf.\n'
		'If you don\'t know what this means, type Y ;)\n\n'
		'Do you want to continue?',
		abort=True)

	setup_procfile(chair_path, yes=True)

	# if production setup
	if os.path.exists(os.path.join(chair_path, 'config', 'supervisor.conf')):
		generate_supervisor_config(chair_path, yes=True)
