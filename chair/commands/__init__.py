# imports - third party imports
import click

# imports - module imports
from chair.utils.cli import (
	MultiCommandGroup,
	print_chair_version,
	use_experimental_feature,
	setup_verbosity,
)


@click.group(cls=MultiCommandGroup)
@click.option(
	"--version",
	is_flag=True,
	is_eager=True,
	callback=print_chair_version,
	expose_value=False,
)
@click.option(
	"--use-feature", is_eager=True, callback=use_experimental_feature, expose_value=False,
)
@click.option(
	"-v", "--verbose", is_flag=True, callback=setup_verbosity, expose_value=False,
)
def chair_command(chair_path="."):
	import chair

	chair.set_vmraid_version(chair_path=chair_path)


from chair.commands.make import (
	drop,
	exclude_app_for_update,
	get_app,
	include_app_for_update,
	init,
	new_app,
	pip,
	remove_app,
)

chair_command.add_command(init)
chair_command.add_command(drop)
chair_command.add_command(get_app)
chair_command.add_command(new_app)
chair_command.add_command(remove_app)
chair_command.add_command(exclude_app_for_update)
chair_command.add_command(include_app_for_update)
chair_command.add_command(pip)


from chair.commands.update import (
	retry_upgrade,
	switch_to_branch,
	switch_to_develop,
	update,
)

chair_command.add_command(update)
chair_command.add_command(retry_upgrade)
chair_command.add_command(switch_to_branch)
chair_command.add_command(switch_to_develop)


from chair.commands.utils import (
	backup_all_sites,
	backup_site,
	chair_src,
	clear_command_cache,
	disable_production,
	download_translations,
	find_chaires,
	generate_command_cache,
	migrate_env,
	prepare_beta_release,
	release,
	renew_lets_encrypt,
	restart,
	set_mariadb_host,
	set_nginx_port,
	set_redis_cache_host,
	set_redis_queue_host,
	set_redis_socketio_host,
	set_ssl_certificate,
	set_ssl_certificate_key,
	set_url_root,
	start,
)

chair_command.add_command(start)
chair_command.add_command(restart)
chair_command.add_command(set_nginx_port)
chair_command.add_command(set_ssl_certificate)
chair_command.add_command(set_ssl_certificate_key)
chair_command.add_command(set_url_root)
chair_command.add_command(set_mariadb_host)
chair_command.add_command(set_redis_cache_host)
chair_command.add_command(set_redis_queue_host)
chair_command.add_command(set_redis_socketio_host)
chair_command.add_command(download_translations)
chair_command.add_command(backup_site)
chair_command.add_command(backup_all_sites)
chair_command.add_command(release)
chair_command.add_command(renew_lets_encrypt)
chair_command.add_command(disable_production)
chair_command.add_command(chair_src)
chair_command.add_command(prepare_beta_release)
chair_command.add_command(find_chaires)
chair_command.add_command(migrate_env)
chair_command.add_command(generate_command_cache)
chair_command.add_command(clear_command_cache)

from chair.commands.setup import setup

chair_command.add_command(setup)


from chair.commands.config import config

chair_command.add_command(config)

from chair.commands.git import remote_reset_url, remote_set_url, remote_urls

chair_command.add_command(remote_set_url)
chair_command.add_command(remote_reset_url)
chair_command.add_command(remote_urls)

from chair.commands.install import install

chair_command.add_command(install)
