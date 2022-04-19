import click
from chair.config.redis import generate_config

def execute(chair_path):
	click.confirm('\nThis update will replace ERPAdda\'s Redis configuration files to fix a major security issue.\n'
		'If you don\'t know what this means, type Y ;)\n\n'
		'Do you want to continue?',
		abort=True)

	generate_config(chair_path)
