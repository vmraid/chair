import click
from click.core import _check_multicommand


def print_chair_version(ctx, param, value):
	"""Prints current chair version"""
	if not value or ctx.resilient_parsing:
		return

	import chair

	click.echo(chair.VERSION)
	ctx.exit()


class MultiCommandGroup(click.Group):
	def add_command(self, cmd, name=None):
		"""Registers another :class:`Command` with this group.  If the name
		is not provided, the name of the command is used.

		Note: This is a custom Group that allows passing a list of names for
		the command name.
		"""
		name = name or cmd.name
		if name is None:
			raise TypeError("Command has no name.")
		_check_multicommand(self, name, cmd, register=True)

		try:
			self.commands[name] = cmd
		except TypeError:
			if isinstance(name, list):
				for _name in name:
					self.commands[_name] = cmd


def use_experimental_feature(ctx, param, value):
	if not value:
		return

	if value == "dynamic-feed":
		import chair.cli

		chair.cli.dynamic_feed = True
		chair.cli.verbose = True
	else:
		from chair.exceptions import FeatureDoesNotExistError

		raise FeatureDoesNotExistError(f"Feature {value} does not exist")

	from chair.cli import is_envvar_warn_set

	if is_envvar_warn_set:
		return

	click.secho(
		"WARNING: chair is using it's new CLI rendering engine. This behaviour has"
		f" been enabled by passing --{value} in the command. This feature is"
		" experimental and may not be implemented for all commands yet.",
		fg="yellow",
	)


def setup_verbosity(ctx, param, value):
	if not value:
		return

	import chair.cli

	chair.cli.verbose = True
