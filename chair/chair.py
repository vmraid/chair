# imports - standard imports
import subprocess
import functools
import os
import shutil
import json
import sys
import logging
from typing import List, MutableSequence, TYPE_CHECKING, Union

# imports - module imports
import chair
from chair.exceptions import ValidationError
from chair.config.common_site_config import setup_config
from chair.utils import (
	paths_in_chair,
	exec_cmd,
	is_chair_directory,
	is_vmraid_app,
	get_cmd_output,
	get_git_version,
	log,
	run_vmraid_cmd,
)
from chair.utils.chair import (
	validate_app_installed_on_sites,
	restart_supervisor_processes,
	restart_systemd_processes,
	restart_process_manager,
	remove_backups_crontab,
	get_venv_path,
	get_env_cmd,
)
from chair.utils.render import job, step
from chair.utils.app import get_current_version


if TYPE_CHECKING:
	from chair.app import App

logger = logging.getLogger(chair.PROJECT_NAME)


class Base:
	def run(self, cmd, cwd=None):
		return exec_cmd(cmd, cwd=cwd or self.cwd)


class Validator:
	def validate_app_uninstall(self, app):
		if app not in self.apps:
			raise ValidationError(f"No app named {app}")
		validate_app_installed_on_sites(app, chair_path=self.name)


@functools.lru_cache(maxsize=None)
class Chair(Base, Validator):
	def __init__(self, path):
		self.name = path
		self.cwd = os.path.abspath(path)
		self.exists = is_chair_directory(self.name)

		self.setup = ChairSetup(self)
		self.teardown = ChairTearDown(self)
		self.apps = ChairApps(self)

		self.apps_txt = os.path.join(self.name, "sites", "apps.txt")
		self.excluded_apps_txt = os.path.join(self.name, "sites", "excluded_apps.txt")

	@property
	def python(self) -> str:
		return get_env_cmd("python", chair_path=self.name)

	@property
	def shallow_clone(self) -> bool:
		config = self.conf

		if config:
			if config.get("release_chair") or not config.get("shallow_clone"):
				return False

		return get_git_version() > 1.9

	@property
	def excluded_apps(self) -> List:
		try:
			with open(self.excluded_apps_txt) as f:
				return f.read().strip().split("\n")
		except Exception:
			return []

	@property
	def sites(self) -> List:
		return [
			path
			for path in os.listdir(os.path.join(self.name, "sites"))
			if os.path.exists(os.path.join("sites", path, "site_config.json"))
		]

	@property
	def conf(self):
		from chair.config.common_site_config import get_config

		return get_config(self.name)

	def init(self):
		self.setup.dirs()
		self.setup.env()
		self.setup.backups()

	def drop(self):
		self.teardown.backups()
		self.teardown.dirs()

	def install(self, app, branch=None):
		from chair.app import App

		app = App(app, branch=branch)
		self.apps.append(app)
		self.apps.sync()

	def uninstall(self, app):
		from chair.app import App

		self.validate_app_uninstall(app)
		self.apps.remove(App(app, chair=self, to_clone=False))
		self.apps.sync()
		# self.build() - removed because it seems unnecessary
		self.reload()

	@step(title="Building Chair Assets", success="Chair Assets Built")
	def build(self):
		# build assets & stuff
		run_vmraid_cmd("build", chair_path=self.name)

	@step(title="Reloading Chair Processes", success="Chair Processes Reloaded")
	def reload(self, web=False, supervisor=True, systemd=True):
		"""If web is True, only web workers are restarted
		"""
		conf = self.conf

		if conf.get("developer_mode"):
			restart_process_manager(chair_path=self.name, web_workers=web)
		if supervisor and conf.get("restart_supervisor_on_update"):
			restart_supervisor_processes(chair_path=self.name, web_workers=web)
		if systemd and conf.get("restart_systemd_on_update"):
			restart_systemd_processes(chair_path=self.name, web_workers=web)

	def get_installed_apps(self) -> List:
		"""Returns list of installed apps on chair, not in excluded_apps.txt
		"""
		apps = [app for app in self.apps if app not in self.excluded_apps]
		apps.remove("vmraid")
		apps.insert(0, "vmraid")
		return apps


class ChairApps(MutableSequence):
	def __init__(self, chair: Chair):
		self.chair = chair
		self.states_path = os.path.join(self.chair.name, "sites", "apps.json")
		self.apps_path = os.path.join(self.chair.name, "apps")
		self.initialize_apps()
		self.set_states()

	def set_states(self):
		try:
			with open(self.states_path, "r") as f:
				self.states = json.loads(f.read() or "{}")
		except FileNotFoundError:
			self.states = {}

	def update_apps_states(self, app_name: Union[str, None] = None, branch: Union[str, None] = None, required:List = []):
		if self.apps and not os.path.exists(self.states_path):
			# idx according to apps listed in apps.txt (backwards compatibility)
			# Keeping vmraid as the first app.
			if "vmraid" in self.apps:
				self.apps.remove("vmraid")
				self.apps.insert(0, "vmraid")
				with open(self.chair.apps_txt, "w") as f:
					f.write("\n".join(self.apps))

			print("Found existing apps updating states...")
			for idx, app in enumerate(self.apps, start=1):
				self.states[app] = {
					"resolution": {
					"commit_hash": None,
					"branch": None
				},
				"required": required,
				"idx": idx,
				"version": get_current_version(app, self.chair.name),
				}

		apps_to_remove = []
		for app in self.states:
			if app not in self.apps:
				apps_to_remove.append(app)

		for app in apps_to_remove:
			del self.states[app]

		if app_name and app_name not in self.states:
			version = get_current_version(app_name, self.chair.name)

			app_dir = os.path.join(self.apps_path, app_name)
			if not branch:
				branch = (
						subprocess
						.check_output("git rev-parse --abbrev-ref HEAD", shell=True, cwd=app_dir)
						.decode("utf-8")
						.rstrip()
						)

			commit_hash = subprocess.check_output(f"git rev-parse {branch}", shell=True, cwd=app_dir).decode("utf-8").rstrip()

			self.states[app_name] = {
				"resolution": {
					"commit_hash":commit_hash,
					"branch": branch
				},
				"required":required,
				"idx":len(self.states) + 1,
				"version": version,
			}

		with open(self.states_path, "w") as f:
			f.write(json.dumps(self.states, indent=4))

	def sync(self,app_name: Union[str, None] = None, branch: Union[str, None] = None, required:List = []):
		self.initialize_apps()
		with open(self.chair.apps_txt, "w") as f:
			f.write("\n".join(self.apps))
		self.update_apps_states(app_name, branch, required)

	def initialize_apps(self):
		is_installed = lambda app: app in installed_packages

		try:
			installed_packages = get_cmd_output(f"{self.chair.python} -m pip freeze", cwd=self.chair.name)
		except Exception:
			self.apps = []
			return

		try:
			self.apps = [
				x
				for x in os.listdir(os.path.join(self.chair.name, "apps"))
				if (
					is_vmraid_app(os.path.join(self.chair.name, "apps", x))
					and is_installed(x)
				)
			]
		except FileNotFoundError:
			self.apps = []

	def __getitem__(self, key):
		""" retrieves an item by its index, key"""
		return self.apps[key]

	def __setitem__(self, key, value):
		""" set the item at index, key, to value """
		# should probably not be allowed
		# self.apps[key] = value
		raise NotImplementedError

	def __delitem__(self, key):
		""" removes the item at index, key """
		# TODO: uninstall and delete app from chair
		del self.apps[key]

	def __len__(self):
		return len(self.apps)

	def insert(self, key, value):
		""" add an item, value, at index, key. """
		# TODO: fetch and install app to chair
		self.apps.insert(key, value)

	def add(self, app: "App"):
		app.get()
		app.install()
		super().append(app.repo)
		self.apps.sort()

	def remove(self, app: "App"):
		app.uninstall()
		app.remove()
		super().remove(app.repo)

	def append(self, app: "App"):
		return self.add(app)

	def __repr__(self):
		return self.__str__()

	def __str__(self):
		return str([x for x in self.apps])


class ChairSetup(Base):
	def __init__(self, chair: Chair):
		self.chair = chair
		self.cwd = self.chair.cwd

	@step(title="Setting Up Directories", success="Directories Set Up")
	def dirs(self):
		os.makedirs(self.chair.name, exist_ok=True)

		for dirname in paths_in_chair:
			os.makedirs(os.path.join(self.chair.name, dirname), exist_ok=True)

	@step(title="Setting Up Environment", success="Environment Set Up")
	def env(self, python="python3"):
		"""Setup env folder
		- create env if not exists
		- upgrade env pip
		- install vmraid python dependencies
		"""
		import chair.cli
		import click

		click.secho("Setting Up Environment", fg="yellow")

		vmraid = os.path.join(self.chair.name, "apps", "vmraid")
		virtualenv = get_venv_path()
		quiet_flag = "" if chair.cli.verbose else "--quiet"

		if not os.path.exists(self.chair.python):
			self.run(f"{virtualenv} {quiet_flag} env -p {python}")

		self.pip()

		if os.path.exists(vmraid):
			self.run(f"{self.chair.python} -m pip install {quiet_flag} --upgrade -e {vmraid}")

	@step(title="Setting Up Chair Config", success="Chair Config Set Up")
	def config(self, redis=True, procfile=True):
		"""Setup config folder
		- create pids folder
		- generate sites/common_site_config.json
		"""
		setup_config(self.chair.name)

		if redis:
			from chair.config.redis import generate_config

			generate_config(self.chair.name)

		if procfile:
			from chair.config.procfile import setup_procfile

			setup_procfile(self.chair.name, skip_redis=not redis)

	@step(title="Updating pip", success="Updated pip")
	def pip(self, verbose=False):
		"""Updates env pip; assumes that env is setup
		"""
		import chair.cli

		verbose = chair.cli.verbose or verbose
		quiet_flag = "" if verbose else "--quiet"

		return self.run(f"{self.chair.python} -m pip install {quiet_flag} --upgrade pip")

	def logging(self):
		from chair.utils import setup_logging

		return setup_logging(chair_path=self.chair.name)

	@step(title="Setting Up Chair Patches", success="Chair Patches Set Up")
	def patches(self):
		shutil.copy(
			os.path.join(os.path.dirname(os.path.abspath(__file__)), "patches", "patches.txt"),
			os.path.join(self.chair.name, "patches.txt"),
		)

	@step(title="Setting Up Backups Cronjob", success="Backups Cronjob Set Up")
	def backups(self):
		# TODO: to something better for logging data? - maybe a wrapper that auto-logs with more context
		logger.log("setting up backups")

		from crontab import CronTab

		chair_dir = os.path.abspath(self.chair.name)
		user = self.chair.conf.get("vmraid_user")
		logfile = os.path.join(chair_dir, "logs", "backup.log")
		system_crontab = CronTab(user=user)
		backup_command = f"cd {chair_dir} && {sys.argv[0]} --verbose --site all backup"
		job_command = f"{backup_command} >> {logfile} 2>&1"

		if job_command not in str(system_crontab):
			job = system_crontab.new(
				command=job_command, comment="chair auto backups set for every 6 hours"
			)
			job.every(6).hours()
			system_crontab.write()

		logger.log("backups were set up")

	@job(title="Setting Up Chair Dependencies", success="Chair Dependencies Set Up")
	def requirements(self, apps=None):
		"""Install and upgrade specified / all installed apps on given Chair
		"""
		from chair.app import App

		if not apps:
			apps = self.chair.get_installed_apps()

		self.pip()

		print(f"Installing {len(apps)} applications...")

		for app in apps:
			App(app, chair=self.chair, to_clone=False).install(
				skip_assets=True, restart_chair=False, ignore_resolution=True
			)

	def python(self, apps=None):
		"""Install and upgrade Python dependencies for specified / all installed apps on given Chair
		"""
		import chair.cli

		if not apps:
			apps = self.chair.get_installed_apps()

		quiet_flag = "" if chair.cli.verbose else "--quiet"

		self.pip()

		for app in apps:
			app_path = os.path.join(self.chair.name, "apps", app)
			log(f"\nInstalling python dependencies for {app}", level=3, no_log=True)
			self.run(f"{self.chair.python} -m pip install {quiet_flag} --upgrade -e {app_path}")

	def node(self, apps=None):
		"""Install and upgrade Node dependencies for specified / all apps on given Chair
		"""
		from chair.utils.chair import update_node_packages

		return update_node_packages(chair_path=self.chair.name, apps=apps)


class ChairTearDown:
	def __init__(self, chair):
		self.chair = chair

	def backups(self):
		remove_backups_crontab(self.chair.name)

	def dirs(self):
		shutil.rmtree(self.chair.name)
