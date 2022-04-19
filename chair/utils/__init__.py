# imports - standard imports
import json
import logging
import os
import subprocess
import re
import sys
from glob import glob
from shlex import split
from typing import List, Tuple
from functools import lru_cache

# imports - third party imports
import click
import requests

# imports - module imports
from chair import PROJECT_NAME, VERSION

from chair.exceptions import CommandFailedError, InvalidRemoteException, ValidationError


logger = logging.getLogger(PROJECT_NAME)
chair_cache_file = ".chair.cmd"
paths_in_app = ("hooks.py", "modules.txt", "patches.txt")
paths_in_chair = ("apps", "sites", "config", "logs", "config/pids")
sudoers_file = "/etc/sudoers.d/vmraid"


def is_chair_directory(directory=os.path.curdir):
	is_chair = True

	for folder in paths_in_chair:
		path = os.path.abspath(os.path.join(directory, folder))
		is_chair = is_chair and os.path.exists(path)

	return is_chair


def is_vmraid_app(directory: str) -> bool:
	is_vmraid_app = True

	for folder in paths_in_app:
		if not is_vmraid_app:
			break

		path = glob(os.path.join(directory, "**", folder))
		is_vmraid_app = is_vmraid_app and path

	return bool(is_vmraid_app)


def is_valid_vmraid_branch(vmraid_path:str, vmraid_branch:str):
	""" Check if a branch exists in a repo. Throws InvalidRemoteException if branch is not found

	Uses github's api without auth to query branch.
	If rate limited by gitapi, requests are sent to github.com

	:param vmraid_path: git url
	:type vmraid_path: str
	:param vmraid_branch: branch to check
	:type vmraid_branch: str
	:raises InvalidRemoteException: branch for this repo doesn't exist
	"""
	if "http" in vmraid_path and vmraid_branch:
		vmraid_path = vmraid_path.replace(".git", "")
		try:
			owner, repo = vmraid_path.split("/")[3], vmraid_path.split("/")[4]
		except IndexError:
			raise InvalidRemoteException("Invalid git url")
		git_api_req = f"https://api.github.com/repos/{owner}/{repo}/branches"
		res = requests.get(git_api_req).json()

		if "message" in res:
			# slower alternative with no rate limit
			github_req = f'https://github.com/{owner}/{repo}/tree/{vmraid_branch}'
			if requests.get(github_req).status_code != 200:
				raise InvalidRemoteException("Invalid git url")

		elif vmraid_branch not in [x["name"] for x in res]:
			raise InvalidRemoteException("VMRaid branch does not exist")


def log(message, level=0, no_log=False):
	import chair
	import chair.cli

	levels = {
		0: ("blue", "INFO"),  # normal
		1: ("green", "SUCCESS"),  # success
		2: ("red", "ERROR"),  # fail
		3: ("yellow", "WARN"),  # warn/suggest
	}

	color, prefix = levels.get(level, levels[0])

	if chair.cli.from_command_line and chair.cli.dynamic_feed:
		chair.LOG_BUFFER.append({"prefix": prefix, "message": message, "color": color})

	if no_log:
		click.secho(message, fg=color)
	else:
		loggers = {2: logger.error, 3: logger.warning}
		level_logger = loggers.get(level, logger.info)

		level_logger(message)
		click.secho(f"{prefix}: {message}", fg=color)


def check_latest_version():
	if VERSION.endswith("dev"):
		return

	import requests
	from semantic_version import Version

	try:
		pypi_request = requests.get("https://pypi.org/pypi/vmraid-chair/json")
	except Exception:
		# Exceptions thrown are defined in requests.exceptions
		# ignore checking on all Exceptions
		return

	if pypi_request.status_code == 200:
		pypi_version_str = pypi_request.json().get("info").get("version")
		pypi_version = Version(pypi_version_str)
		local_version = Version(VERSION)

		if pypi_version > local_version:
			log(f"A newer version of chair is available: {local_version} → {pypi_version}")


def pause_exec(seconds=10):
	from time import sleep

	for i in range(seconds, 0, -1):
		print(f"Will continue execution in {i} seconds...", end="\r")
		sleep(1)

	print(" " * 40, end="\r")


def exec_cmd(cmd, cwd=".", env=None, _raise=True):
	if env:
		env.update(os.environ.copy())

	click.secho(f"$ {cmd}", fg="bright_black")

	cwd_info = f"cd {cwd} && " if cwd != "." else ""
	cmd_log = f"{cwd_info}{cmd}"
	logger.debug(cmd_log)
	cmd = split(cmd)
	return_code = subprocess.call(cmd, cwd=cwd, universal_newlines=True, env=env)
	if return_code:
		logger.warning(f"{cmd_log} executed with exit code {return_code}")
		if _raise:
			raise CommandFailedError
	return return_code


def which(executable: str, raise_err: bool = False) -> str:
	from shutil import which

	exec_ = which(executable)

	if not exec_ and raise_err:
		raise FileNotFoundError(f"{executable} not found in PATH")

	return exec_


def setup_logging(chair_path=".") -> "logger":
	LOG_LEVEL = 15
	logging.addLevelName(LOG_LEVEL, "LOG")

	def logv(self, message, *args, **kws):
		if self.isEnabledFor(LOG_LEVEL):
			self._log(LOG_LEVEL, message, args, **kws)

	logging.Logger.log = logv

	if os.path.exists(os.path.join(chair_path, "logs")):
		log_file = os.path.join(chair_path, "logs", "chair.log")
		hdlr = logging.FileHandler(log_file)
	else:
		hdlr = logging.NullHandler()

	logger = logging.getLogger(PROJECT_NAME)
	formatter = logging.Formatter("%(asctime)s %(levelname)s %(message)s")
	hdlr.setFormatter(formatter)
	logger.addHandler(hdlr)
	logger.setLevel(logging.DEBUG)

	return logger


def get_process_manager() -> str:
	for proc_man in ["honcho", "foreman", "forego"]:
		proc_man_path = which(proc_man)
		if proc_man_path:
			return proc_man_path


def get_git_version() -> float:
	"""returns git version from `git --version`
	extracts version number from string `get version 1.9.1` etc"""
	version = get_cmd_output("git --version")
	version = version.strip().split()[2]
	version = ".".join(version.split(".")[0:2])
	return float(version)


def get_cmd_output(cmd, cwd=".", _raise=True):
	output = ""
	try:
		output = subprocess.check_output(cmd, cwd=cwd, shell=True, stderr=subprocess.PIPE, encoding="utf-8").strip()
	except subprocess.CalledProcessError as e:
		if e.output:
			output = e.output
		elif _raise:
			raise
	return output


def is_root():
	return os.getuid() == 0


def run_vmraid_cmd(*args, **kwargs):
	from chair.cli import from_command_line
	from chair.utils.chair import get_env_cmd

	chair_path = kwargs.get("chair_path", ".")
	f = get_env_cmd("python", chair_path=chair_path)
	sites_dir = os.path.join(chair_path, "sites")

	is_async = False if from_command_line else True
	if is_async:
		stderr = stdout = subprocess.PIPE
	else:
		stderr = stdout = None

	p = subprocess.Popen(
		(f, "-m", "vmraid.utils.chair_helper", "vmraid") + args,
		cwd=sites_dir,
		stdout=stdout,
		stderr=stderr,
	)

	if is_async:
		return_code = print_output(p)
	else:
		return_code = p.wait()

	if return_code > 0:
		sys.exit(return_code)


def print_output(p):
	from select import select

	while p.poll() is None:
		readx = select([p.stdout.fileno(), p.stderr.fileno()], [], [])[0]
		send_buffer = []
		for fd in readx:
			if fd == p.stdout.fileno():
				while 1:
					buf = p.stdout.read(1)
					if not len(buf):
						break
					if buf == "\r" or buf == "\n":
						send_buffer.append(buf)
						log_line("".join(send_buffer), "stdout")
						send_buffer = []
					else:
						send_buffer.append(buf)

			if fd == p.stderr.fileno():
				log_line(p.stderr.readline(), "stderr")
	return p.poll()


def log_line(data, stream):
	if stream == "stderr":
		return sys.stderr.write(data)
	return sys.stdout.write(data)


def get_chair_name(chair_path):
	return os.path.basename(os.path.abspath(chair_path))


def set_git_remote_url(git_url, chair_path="."):
	"Set app remote git url"
	from chair.app import get_repo_dir
	from chair.chair import Chair

	app = git_url.rsplit("/", 1)[1].rsplit(".", 1)[0]

	if app not in Chair(chair_path).apps:
		raise ValidationError(f"No app named {app}")

	app_dir = get_repo_dir(app, chair_path=chair_path)

	if os.path.exists(os.path.join(app_dir, ".git")):
		exec_cmd(f"git remote set-url upstream {git_url}", cwd=app_dir)


def run_playbook(playbook_name, extra_vars=None, tag=None):
	import chair

	if not which("ansible"):
		print(
			"Ansible is needed to run this command, please install it using 'pip"
			" install ansible'"
		)
		sys.exit(1)
	args = ["ansible-playbook", "-c", "local", playbook_name, "-vvvv"]

	if extra_vars:
		args.extend(["-e", json.dumps(extra_vars)])

	if tag:
		args.extend(["-t", tag])

	subprocess.check_call(args, cwd=os.path.join(chair.__path__[0], "playbooks"))


def find_chaires(directory: str = None) -> List:
	if not directory:
		directory = os.path.expanduser("~")
	elif os.path.exists(directory):
		directory = os.path.abspath(directory)
	else:
		log("Directory doesn't exist", level=2)
		sys.exit(1)

	if is_chair_directory(directory):
		if os.path.curdir == directory:
			print("You are in a chair directory!")
		else:
			print(f"{directory} is a chair directory!")
		return

	chaires = []

	try:
		sub_directories = os.listdir(directory)
	except PermissionError:
		return chaires

	for sub in sub_directories:
		sub = os.path.join(directory, sub)
		if os.path.isdir(sub) and not os.path.islink(sub):
			if is_chair_directory(sub):
				print(f"{sub} found!")
				chaires.append(sub)
			else:
				chaires.extend(find_chaires(sub))

	return chaires


def is_dist_editable(dist: str) -> bool:
	"""Is distribution an editable install?"""
	for path_item in sys.path:
		egg_link = os.path.join(path_item, f"{dist}.egg-link")
		if os.path.isfile(egg_link):
			return True
	return False


def find_parent_chair(path: str) -> str:
	"""Checks if parent directories are chaires"""
	if is_chair_directory(directory=path):
		return path

	home_path = os.path.expanduser("~")
	root_path = os.path.abspath(os.sep)

	if path not in {home_path, root_path}:
		# NOTE: the os.path.split assumes that given path is absolute
		parent_dir = os.path.split(path)[0]
		return find_parent_chair(parent_dir)


def generate_command_cache(chair_path=".") -> List:
	"""Caches all available commands (even custom apps) via VMRaid
	Default caching behaviour: generated the first time any command (for a specific chair directory)
	"""
	from chair.utils.chair import get_env_cmd

	python = get_env_cmd("python", chair_path=chair_path)
	sites_path = os.path.join(chair_path, "sites")

	if os.path.exists(chair_cache_file):
		os.remove(chair_cache_file)

	try:
		output = get_cmd_output(
			f"{python} -m vmraid.utils.chair_helper get-vmraid-commands", cwd=sites_path
		)
		with open(chair_cache_file, "w") as f:
			json.dump(eval(output), f)
		return json.loads(output)

	except subprocess.CalledProcessError as e:
		if hasattr(e, "stderr"):
			print(e.stderr)

	return []


def clear_command_cache(chair_path="."):
	"""Clears commands cached
	Default invalidation behaviour: destroyed on each run of `chair update`
	"""

	if os.path.exists(chair_cache_file):
		os.remove(chair_cache_file)
	else:
		print("Chair command cache doesn't exist in this folder!")


def find_org(org_repo):
	import requests

	org_repo = org_repo[0]

	for org in ["vmraid", "erpadda"]:
		res = requests.head(f"https://api.github.com/repos/{org}/{org_repo}")
		if res.status_code in (400, 403):
			res = requests.head(f"https://github.com/{org}/{org_repo}")
		if res.ok:
			return org, org_repo

	raise InvalidRemoteException(f"{org_repo} Not foung in vmraid or erpadda")


def fetch_details_from_tag(_tag: str) -> Tuple[str, str, str]:
	if not _tag:
		raise Exception("Tag is not provided")

	app_tag = _tag.split("@")
	org_repo = app_tag[0].split("/")

	try:
		repo, tag = app_tag
	except ValueError:
		repo, tag = app_tag + [None]

	try:
		org, repo = org_repo
	except Exception:
		org, repo = find_org(org_repo)

	return org, repo, tag


def is_git_url(url: str) -> bool:
	# modified to allow without the tailing .git from https://github.com/jonschlinkert/is-git-url.git
	pattern = r"(?:git|ssh|https?|\w*@[-\w.]+):(\/\/)?(.*?)(\.git)?(\/?|\#[-\d\w._]+?)$"
	return bool(re.match(pattern, url))


def drop_privileges(uid_name="nobody", gid_name="nogroup"):
	import grp
	import pwd

	# from http://stackoverflow.com/a/2699996
	if os.getuid() != 0:
		# We're not root so, like, whatever dude
		return

	# Get the uid/gid from the name
	running_uid = pwd.getpwnam(uid_name).pw_uid
	running_gid = grp.getgrnam(gid_name).gr_gid

	# Remove group privileges
	os.setgroups([])

	# Try setting the new uid/gid
	os.setgid(running_gid)
	os.setuid(running_uid)

	# Ensure a very conservative umask
	os.umask(0o22)


def get_available_folder_name(name: str, path: str) -> str:
	"""Subfixes the passed name with -1 uptil -100 whatever's available"""
	if os.path.exists(os.path.join(path, name)):
		for num in range(1, 100):
			_dt = f"{name}_{num}"
			if not os.path.exists(os.path.join(path, _dt)):
				return _dt
	return name


def get_traceback() -> str:
	"""Returns the traceback of the Exception"""
	from traceback import format_exception

	exc_type, exc_value, exc_tb = sys.exc_info()

	if not any([exc_type, exc_value, exc_tb]):
		return ""

	trace_list = format_exception(exc_type, exc_value, exc_tb)
	return "".join(trace_list)


class _dict(dict):
	"""dict like object that exposes keys as attributes"""
	# chair port of vmraid._dict
	def __getattr__(self, key):
		ret = self.get(key)
		# "__deepcopy__" exception added to fix vmraid#14833 via DFP
		if not ret and key.startswith("__") and key != "__deepcopy__":
			raise AttributeError()
		return ret
	def __setattr__(self, key, value):
		self[key] = value
	def __getstate__(self):
		return self
	def __setstate__(self, d):
		self.update(d)
	def update(self, d):
		"""update and return self -- the missing dict feature in python"""
		super(_dict, self).update(d)
		return self
	def copy(self):
		return _dict(dict(self).copy())


def parse_sys_argv():
	sys_argv = _dict(options=set(), commands=set())

	for c in sys.argv[1:]:
		if c.startswith("-"):
			sys_argv.options.add(c)
		else:
			sys_argv.commands.add(c)

	return sys_argv
