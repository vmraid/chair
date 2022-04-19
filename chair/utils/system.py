# imports - standard imports
import grp
import os
import pwd
import shutil
import sys

# imports - module imports
import chair
from chair.utils import (
	exec_cmd,
	get_process_manager,
	log,
	run_vmraid_cmd,
	sudoers_file,
	which,
	is_valid_vmraid_branch,
)
from chair.utils.chair import build_assets, clone_apps_from
from chair.utils.render import job


@job(title="Initializing Chair {path}", success="Chair {path} initialized")
def init(
	path,
	apps_path=None,
	no_procfile=False,
	no_backups=False,
	vmraid_path=None,
	vmraid_branch=None,
	verbose=False,
	clone_from=None,
	skip_redis_config_generation=False,
	clone_without_update=False,
	skip_assets=False,
	python="python3",
	install_app=None,
):
	"""Initialize a new chair directory

	* create a chair directory in the given path
	* setup logging for the chair
	* setup env for the chair
	* setup config (dir/pids/redis/procfile) for the chair
	* setup patches.txt for chair
	* clone & install vmraid
		* install python & node dependencies
		* build assets
	* setup backups crontab
	"""

	# Use print("\033c", end="") to clear entire screen after each step and re-render each list
	# another way => https://stackoverflow.com/a/44591228/10309266

	import chair.cli
	from chair.app import get_app, install_apps_from_path
	from chair.chair import Chair

	verbose = chair.cli.verbose or verbose

	chair = Chair(path)

	chair.setup.dirs()
	chair.setup.logging()
	chair.setup.env(python=python)
	chair.setup.config(redis=not skip_redis_config_generation, procfile=not no_procfile)
	chair.setup.patches()

	# local apps
	if clone_from:
		clone_apps_from(
			chair_path=path, clone_from=clone_from, update_app=not clone_without_update
		)

	# remote apps
	else:
		vmraid_path = vmraid_path or "https://github.com/vmraid/vmraid.git"
		is_valid_vmraid_branch(vmraid_path=vmraid_path, vmraid_branch=vmraid_branch)
		get_app(
			vmraid_path,
			branch=vmraid_branch,
			chair_path=path,
			skip_assets=True,
			verbose=verbose,
			resolve_deps=False,
		)

		# fetch remote apps using config file - deprecate this!
		if apps_path:
			install_apps_from_path(apps_path, chair_path=path)

	# getting app on chair init using --install-app
	if install_app:
		get_app(
			install_app,
			branch=vmraid_branch,
			chair_path=path,
			skip_assets=True,
			verbose=verbose,
			resolve_deps=False,
		)

	if not skip_assets:
		build_assets(chair_path=path)

	if not no_backups:
		chair.setup.backups()


def setup_sudoers(user):
	if not os.path.exists("/etc/sudoers.d"):
		os.makedirs("/etc/sudoers.d")

		set_permissions = False
		if not os.path.exists("/etc/sudoers"):
			set_permissions = True

		with open("/etc/sudoers", "a") as f:
			f.write("\n#includedir /etc/sudoers.d\n")

		if set_permissions:
			os.chmod("/etc/sudoers", 0o440)

	template = chair.config.env().get_template("vmraid_sudoers")
	vmraid_sudoers = template.render(
		**{
			"user": user,
			"service": which("service"),
			"systemctl": which("systemctl"),
			"nginx": which("nginx"),
		}
	)

	with open(sudoers_file, "w") as f:
		f.write(vmraid_sudoers)

	os.chmod(sudoers_file, 0o440)
	log(f"Sudoers was set up for user {user}", level=1)


def start(no_dev=False, concurrency=None, procfile=None, no_prefix=False, procman=None):
	if procman:
		program = which(procman)
	else:
		program = get_process_manager()

	if not program:
		raise Exception("No process manager found")

	os.environ["PYTHONUNBUFFERED"] = "true"
	if not no_dev:
		os.environ["DEV_SERVER"] = "true"

	command = [program, "start"]
	if concurrency:
		command.extend(["-c", concurrency])

	if procfile:
		command.extend(["-f", procfile])

	if no_prefix:
		command.extend(["--no-prefix"])

	os.execv(program, command)


def migrate_site(site, chair_path="."):
	run_vmraid_cmd("--site", site, "migrate", chair_path=chair_path)


def backup_site(site, chair_path="."):
	run_vmraid_cmd("--site", site, "backup", chair_path=chair_path)


def backup_all_sites(chair_path="."):
	from chair.chair import Chair

	for site in Chair(chair_path).sites:
		backup_site(site, chair_path=chair_path)


def fix_prod_setup_perms(chair_path=".", vmraid_user=None):
	from glob import glob
	from chair.chair import Chair

	vmraid_user = vmraid_user or Chair(chair_path).conf.get("vmraid_user")

	if not vmraid_user:
		print("vmraid user not set")
		sys.exit(1)

	globs = ["logs/*", "config/*"]
	for glob_name in globs:
		for path in glob(glob_name):
			uid = pwd.getpwnam(vmraid_user).pw_uid
			gid = grp.getgrnam(vmraid_user).gr_gid
			os.chown(path, uid, gid)


def setup_fonts():
	fonts_path = os.path.join("/tmp", "fonts")

	if os.path.exists("/etc/fonts_backup"):
		return

	exec_cmd("git clone https://github.com/vmraid/fonts.git", cwd="/tmp")
	os.rename("/etc/fonts", "/etc/fonts_backup")
	os.rename("/usr/share/fonts", "/usr/share/fonts_backup")
	os.rename(os.path.join(fonts_path, "etc_fonts"), "/etc/fonts")
	os.rename(os.path.join(fonts_path, "usr_share_fonts"), "/usr/share/fonts")
	shutil.rmtree(fonts_path)
	exec_cmd("fc-cache -fv")
