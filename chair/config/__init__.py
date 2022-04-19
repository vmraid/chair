"""Module for setting up system and respective chair configurations"""


def env():
	from jinja2 import Environment, PackageLoader
	return Environment(loader=PackageLoader('chair.config'))
