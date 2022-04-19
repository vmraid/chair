# imports - standard imports
import json
import logging
import os
import re
import subprocess
import sys
from json.decoder import JSONDecodeError
import typing

# imports - third party imports
import click
import chair

# imports - module imports
from chair.utils import (
	which,
	log,
	exec_cmd,
	get_chair_name,
	get_cmd_output,
)
from chair.exceptions import PatchError, ValidationError


if typing.TYPE_CHECKING:
	from chair.chair import Chair

logger = logging.getLogger(chair.PROJECT_NAME)


def get_env_cmd(cmd, chair_path="."):
	return os.path.abspath(os.path.join(chair_path, "env", "bin", cmd))


def get_venv_path():
	venv = which("virtualenv")

	if not venv:
		current_python = sys.executable
		with open(os.devnull, "wb") as devnull:
			is_venv_installed = not subprocess.call(
				[current_python, "-m", "venv", "--help"], stdout=devnull
			)
		if is_venv_installed:
			venv = f"{current_python} -m venv"

	return venv or log("virtualenv cannot be found", level=2)


def update_node_packages(chair_path=".", apps=None):
	print("Updating node packages...")
	from chair.utils.app import get_develop_version
	from distutils.version import LooseVersion

	v = LooseVersion(get_develop_version("vmraid", chair_path=chair_path))

	# After rollup was merged, vmraid_version = 10.1
	# if develop_verion is 11 and up, only then install yarn
	if v < LooseVersion("11.x.x-develop"):
		update_npm_packages(chair_path, apps=apps)
	else:
		update_yarn_packages(chair_path, apps=apps)


def install_python_dev_dependencies(chair_path=".", apps=None, verbose=False):
	import chair.cli
	from chair.chair import Chair

	verbose = chair.cli.verbose or verbose
	quiet_flag = "" if verbose else "--quiet"

	chair = Chair(chair_path)

	if isinstance(apps, str):
		apps = [apps]
	elif not apps:
		apps = chair.get_installed_apps()

	for app in apps:
		app_path = os.path.join(chair_path, "apps", app)

		dev_requirements_path = os.path.join(app_path, "dev-requirements.txt")

		if os.path.exists(dev_requirements_path):
			chair.run(f"{chair.python} -m pip install {quiet_flag} --upgrade -r {dev_requirements_path}")


def update_yarn_packages(chair_path=".", apps=None):
	from chair.chair import Chair

	chair = Chair(chair_path)

	if not apps:
		apps = chair.get_installed_apps()

	apps_dir = os.path.join(chair.name, "apps")

	# TODO: Check for stuff like this early on only??
	if not which("yarn"):
		print("Please install yarn using below command and try again.")
		print("`npm install -g yarn`")
		return

	for app in apps:
		app_path = os.path.join(apps_dir, app)
		if os.path.exists(os.path.join(app_path, "package.json")):
			click.secho(f"\nInstalling node dependencies for {app}", fg="yellow")
			chair.run("yarn install", cwd=app_path)


def update_npm_packages(chair_path=".", apps=None):
	apps_dir = os.path.join(chair_path, "apps")
	package_json = {}

	if not apps:
		apps = os.listdir(apps_dir)

	for app in apps:
		package_json_path = os.path.join(apps_dir, app, "package.json")

		if os.path.exists(package_json_path):
			with open(package_json_path, "r") as f:
				app_package_json = json.loads(f.read())
				# package.json is usually a dict in a dict
				for key, value in app_package_json.items():
					if key not in package_json:
						package_json[key] = value
					else:
						if isinstance(value, dict):
							package_json[key].update(value)
						elif isinstance(value, list):
							package_json[key].extend(value)
						else:
							package_json[key] = value

	if package_json is {}:
		with open(os.path.join(os.path.dirname(__file__), "package.json"), "r") as f:
			package_json = json.loads(f.read())

	with open(os.path.join(chair_path, "package.json"), "w") as f:
		f.write(json.dumps(package_json, indent=1, sort_keys=True))

	exec_cmd("npm install", cwd=chair_path)


def migrate_env(python, backup=False):
	import shutil
	from urllib.parse import urlparse
	from chair.chair import Chair

	chair = Chair(".")
	nvenv = "env"
	path = os.getcwd()
	python = which(python)
	virtualenv = which("virtualenv")
	pvenv = os.path.join(path, nvenv)

	# Clear Cache before Chair Dies.
	try:
		config = chair.conf
		rredis = urlparse(config["redis_cache"])
		redis = f"{which('redis-cli')} -p {rredis.port}"

		logger.log("Clearing Redis Cache...")
		exec_cmd(f"{redis} FLUSHALL")
		logger.log("Clearing Redis DataBase...")
		exec_cmd(f"{redis} FLUSHDB")
	except Exception:
		logger.warning("Please ensure Redis Connections are running or Daemonized.")

	# Backup venv: restore using `virtualenv --relocatable` if needed
	if backup:
		from datetime import datetime

		parch = os.path.join(path, "archived", "envs")
		os.makedirs(parch, exist_ok=True)

		source = os.path.join(path, "env")
		target = parch

		logger.log("Backing up Virtual Environment")
		stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
		dest = os.path.join(path, str(stamp))

		os.rename(source, dest)
		shutil.move(dest, target)

	# Create virtualenv using specified python
	venv_creation, packages_setup = 1, 1
	try:
		logger.log(f"Setting up a New Virtual {python} Environment")
		venv_creation = exec_cmd(f"{virtualenv} --python {python} {pvenv}")

		apps = " ".join([f"-e {os.path.join('apps', app)}" for app in chair.apps])
		packages_setup = exec_cmd(f"{pvenv} -m pip install --upgrade {apps}")

		logger.log(f"Migration Successful to {python}")
	except Exception:
		if venv_creation or packages_setup:
			logger.warning("Migration Error")


def validate_upgrade(from_ver, to_ver, chair_path="."):
	if to_ver >= 6:
		if not which("npm") and not (which("node") or which("nodejs")):
			raise Exception("Please install nodejs and npm")


def post_upgrade(from_ver, to_ver, chair_path="."):
	from chair.config import redis
	from chair.config.supervisor import generate_supervisor_config
	from chair.config.nginx import make_nginx_conf
	from chair.chair import Chair

	conf = Chair(chair_path).conf
	print("-" * 80 + f"Your chair was upgraded to version {to_ver}")

	if conf.get("restart_supervisor_on_update"):
		redis.generate_config(chair_path=chair_path)
		generate_supervisor_config(chair_path=chair_path)
		make_nginx_conf(chair_path=chair_path)
		print(
			"As you have setup your chair for production, you will have to reload"
			" configuration for nginx and supervisor. To complete the migration, please"
			" run the following commands:\nsudo service nginx restart\nsudo"
			" supervisorctl reload"
		)


def patch_sites(chair_path="."):
	from chair.chair import Chair
	from chair.utils.system import migrate_site

	chair = Chair(chair_path)

	for site in chair.sites:
		try:
			migrate_site(site, chair_path=chair_path)
		except subprocess.CalledProcessError:
			raise PatchError


def restart_supervisor_processes(chair_path=".", web_workers=False):
	from chair.chair import Chair

	chair = Chair(chair_path)
	conf = chair.conf
	cmd = conf.get("supervisor_restart_cmd")
	chair_name = get_chair_name(chair_path)

	if cmd:
		chair.run(cmd)

	else:
		sudo = ""
		try:
			supervisor_status = get_cmd_output("supervisorctl status", cwd=chair_path)
		except Exception as e:
			if e.returncode == 127:
				log("restart failed: Couldn't find supervisorctl in PATH", level=3)
				return
			sudo = "sudo "
			supervisor_status = get_cmd_output("sudo supervisorctl status", cwd=chair_path)

		if web_workers and f"{chair_name}-web:" in supervisor_status:
			group = f"{chair_name}-web:\t"

		elif f"{chair_name}-workers:" in supervisor_status:
			group = f"{chair_name}-workers: {chair_name}-web:"

		# backward compatibility
		elif f"{chair_name}-processes:" in supervisor_status:
			group = f"{chair_name}-processes:"

		# backward compatibility
		else:
			group = "vmraid:"

		chair.run(f"{sudo}supervisorctl restart {group}")


def restart_systemd_processes(chair_path=".", web_workers=False):
	chair_name = get_chair_name(chair_path)
	exec_cmd(
		f"sudo systemctl stop -- $(systemctl show -p Requires {chair_name}.target | cut"
		" -d= -f2)"
	)
	exec_cmd(
		f"sudo systemctl start -- $(systemctl show -p Requires {chair_name}.target |"
		" cut -d= -f2)"
	)


def restart_process_manager(chair_path=".", web_workers=False):
	# only overmind has the restart feature, not sure other supported procmans do
	if which("overmind") and os.path.exists(
		os.path.join(chair_path, ".overmind.sock")
	):
		worker = "web" if web_workers else ""
		exec_cmd(f"overmind restart {worker}", cwd=chair_path)


def build_assets(chair_path=".", app=None):
	command = "chair build"
	if app:
		command += f" --app {app}"
	exec_cmd(command, cwd=chair_path, env={"CHAIR_DEVELOPER": "1"})


def handle_version_upgrade(version_upgrade, chair_path, force, reset, conf):
	from chair.utils import pause_exec, log

	if version_upgrade[0]:
		if force:
			log(
				"""Force flag has been used for a major version change in VMRaid and it's apps.
This will take significant time to migrate and might break custom apps.""",
				level=3,
			)
		else:
			print(
				f"""This update will cause a major version change in VMRaid/ERPAdda from {version_upgrade[1]} to {version_upgrade[2]}.
This would take significant time to migrate and might break custom apps."""
			)
			click.confirm("Do you want to continue?", abort=True)

	if not reset and conf.get("shallow_clone"):
		log(
			"""shallow_clone is set in your chair config.
However without passing the --reset flag, your repositories will be unshallowed.
To avoid this, cancel this operation and run `chair update --reset`.

Consider the consequences of `git reset --hard` on your apps before you run that.
To avoid seeing this warning, set shallow_clone to false in your common_site_config.json
		""",
			level=3,
		)
		pause_exec(seconds=10)

	if version_upgrade[0] or (not version_upgrade[0] and force):
		validate_upgrade(version_upgrade[1], version_upgrade[2], chair_path=chair_path)


def update(
	pull: bool = False,
	apps: str = None,
	patch: bool = False,
	build: bool = False,
	requirements: bool = False,
	backup: bool = True,
	compile: bool = True,
	force: bool = False,
	reset: bool = False,
	restart_supervisor: bool = False,
	restart_systemd: bool = False,
):
	"""command: chair update"""
	import re
	from chair import patches

	from chair.app import pull_apps
	from chair.chair import Chair
	from chair.config.common_site_config import update_config
	from chair.exceptions import CannotUpdateReleaseChair

	from chair.utils import clear_command_cache
	from chair.utils.app import is_version_upgrade
	from chair.utils.system import backup_all_sites

	chair_path = os.path.abspath(".")
	chair = Chair(chair_path)
	patches.run(chair_path=chair_path)
	conf = chair.conf

	clear_command_cache(chair_path=".")

	if conf.get("release_chair"):
		raise CannotUpdateReleaseChair("Release chair detected, cannot update!")

	if not (pull or patch or build or requirements):
		pull, patch, build, requirements = True, True, True, True

	if apps and pull:
		apps = [app.strip() for app in re.split(",| ", apps) if app]
	else:
		apps = []

	validate_branch()

	version_upgrade = is_version_upgrade()
	handle_version_upgrade(version_upgrade, chair_path, force, reset, conf)

	conf.update({"maintenance_mode": 1, "pause_scheduler": 1})
	update_config(conf, chair_path=chair_path)

	if backup:
		print("Backing up sites...")
		backup_all_sites(chair_path=chair_path)

	if pull:
		print("Updating apps source...")
		pull_apps(apps=apps, chair_path=chair_path, reset=reset)

	if requirements:
		print("Setting up requirements...")
		chair.setup.requirements()

	if patch:
		print("Patching sites...")
		patch_sites(chair_path=chair_path)

	if build:
		print("Building assets...")
		chair.build()

	if version_upgrade[0] or (not version_upgrade[0] and force):
		post_upgrade(version_upgrade[1], version_upgrade[2], chair_path=chair_path)

	if pull and compile:
		from compileall import compile_dir

		print("Compiling Python files...")
		apps_dir = os.path.join(chair_path, "apps")
		compile_dir(apps_dir, quiet=1, rx=re.compile(".*node_modules.*"))

	chair.reload(web=False, supervisor=restart_supervisor, systemd=restart_systemd)

	conf.update({"maintenance_mode": 0, "pause_scheduler": 0})
	update_config(conf, chair_path=chair_path)

	print(
		"_" * 80
		+ "\nChair: Deployment tool for VMRaid and VMRaid Applications"
		" (https://vmraid.io/chair).\nOpen source depends on your contributions, so do"
		" give back by submitting bug reports, patches and fixes and be a part of the"
		" community :)"
	)


def clone_apps_from(chair_path, clone_from, update_app=True):
	from chair.app import install_app

	print(f"Copying apps from {clone_from}...")
	subprocess.check_output(["cp", "-R", os.path.join(clone_from, "apps"), chair_path])

	node_modules_path = os.path.join(clone_from, "node_modules")
	if os.path.exists(node_modules_path):
		print(f"Copying node_modules from {clone_from}...")
		subprocess.check_output(["cp", "-R", node_modules_path, chair_path])

	def setup_app(app):
		# run git reset --hard in each branch, pull latest updates and install_app
		app_path = os.path.join(chair_path, "apps", app)

		# remove .egg-ino
		subprocess.check_output(["rm", "-rf", app + ".egg-info"], cwd=app_path)

		if update_app and os.path.exists(os.path.join(app_path, ".git")):
			remotes = subprocess.check_output(["git", "remote"], cwd=app_path).strip().split()
			if "upstream" in remotes:
				remote = "upstream"
			else:
				remote = remotes[0]
			print(f"Cleaning up {app}")
			branch = subprocess.check_output(
				["git", "rev-parse", "--abbrev-ref", "HEAD"], cwd=app_path
			).strip()
			subprocess.check_output(["git", "reset", "--hard"], cwd=app_path)
			subprocess.check_output(["git", "pull", "--rebase", remote, branch], cwd=app_path)

		install_app(app, chair_path, restart_chair=False)

	with open(os.path.join(clone_from, "sites", "apps.txt"), "r") as f:
		apps = f.read().splitlines()

	for app in apps:
		setup_app(app)


def remove_backups_crontab(chair_path="."):
	from crontab import CronTab
	from chair.chair import Chair

	logger.log("removing backup cronjob")

	chair_dir = os.path.abspath(chair_path)
	user = Chair(chair_dir).conf.get("vmraid_user")
	logfile = os.path.join(chair_dir, "logs", "backup.log")
	system_crontab = CronTab(user=user)
	backup_command = f"cd {chair_dir} && {sys.argv[0]} --verbose --site all backup"
	job_command = f"{backup_command} >> {logfile} 2>&1"

	system_crontab.remove_all(command=job_command)


def set_mariadb_host(host, chair_path="."):
	update_common_site_config({"db_host": host}, chair_path=chair_path)


def set_redis_cache_host(host, chair_path="."):
	update_common_site_config({"redis_cache": f"redis://{host}"}, chair_path=chair_path)


def set_redis_queue_host(host, chair_path="."):
	update_common_site_config({"redis_queue": f"redis://{host}"}, chair_path=chair_path)


def set_redis_socketio_host(host, chair_path="."):
	update_common_site_config({"redis_socketio": f"redis://{host}"}, chair_path=chair_path)


def update_common_site_config(ddict, chair_path="."):
	filename = os.path.join(chair_path, "sites", "common_site_config.json")

	if os.path.exists(filename):
		with open(filename, "r") as f:
			content = json.load(f)

	else:
		content = {}

	content.update(ddict)
	with open(filename, "w") as f:
		json.dump(content, f, indent=1, sort_keys=True)


def validate_app_installed_on_sites(app, chair_path="."):
	print("Checking if app installed on active sites...")
	ret = check_app_installed(app, chair_path=chair_path)

	if ret is None:
		check_app_installed_legacy(app, chair_path=chair_path)
	else:
		return ret


def check_app_installed(app, chair_path="."):
	try:
		out = subprocess.check_output(
			["chair", "--site", "all", "list-apps", "--format", "json"],
			stderr=open(os.devnull, "wb"),
			cwd=chair_path,
		).decode("utf-8")
	except subprocess.CalledProcessError:
		return None

	try:
		apps_sites_dict = json.loads(out)
	except JSONDecodeError:
		return None

	for site, apps in apps_sites_dict.items():
		if app in apps:
			raise ValidationError(f"Cannot remove, app is installed on site: {site}")


def check_app_installed_legacy(app, chair_path="."):
	site_path = os.path.join(chair_path, "sites")

	for site in os.listdir(site_path):
		req_file = os.path.join(site_path, site, "site_config.json")
		if os.path.exists(req_file):
			out = subprocess.check_output(
				["chair", "--site", site, "list-apps"], cwd=chair_path
			).decode("utf-8")
			if re.search(r"\b" + app + r"\b", out):
				print(f"Cannot remove, app is installed on site: {site}")
				sys.exit(1)


def validate_branch():
	from chair.chair import Chair
	from chair.utils.app import get_current_branch

	apps = Chair(".").apps

	installed_apps = set(apps)
	check_apps = set(["vmraid", "erpadda"])
	intersection_apps = installed_apps.intersection(check_apps)

	for app in intersection_apps:
		branch = get_current_branch(app)

		if branch == "master":
			print(
				"""'master' branch is renamed to 'version-11' since 'version-12' release.
As of January 2020, the following branches are
version		VMRaid			ERPAdda
11		version-11		version-11
12		version-12		version-12
13		version-13		version-13
14		develop			develop

Please switch to new branches to get future updates.
To switch to your required branch, run the following commands: chair switch-to-branch [branch-name]"""
			)

			sys.exit(1)
