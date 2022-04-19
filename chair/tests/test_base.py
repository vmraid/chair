# imports - standard imports
import getpass
import json
import os
import shutil
import subprocess
import sys
import traceback
import unittest

# imports - module imports
import chair
from chair.utils import paths_in_chair, exec_cmd
from chair.utils.system import init
from chair.chair import Chair

PYTHON_VER = sys.version_info

VMRAID_BRANCH = "version-12"
if PYTHON_VER.major == 3:
	if PYTHON_VER.minor in [6, 7]:
		VMRAID_BRANCH = "version-13"
	else:
		VMRAID_BRANCH = "develop"

class TestChairBase(unittest.TestCase):
	def setUp(self):
		self.chaires_path = "."
		self.chaires = []

	def tearDown(self):
		for chair_name in self.chaires:
			chair_path = os.path.join(self.chaires_path, chair_name)
			chair = Chair(chair_path)
			mariadb_password = "travis" if os.environ.get("CI") else getpass.getpass(prompt="Enter MariaDB root Password: ")

			if chair.exists:
				for site in chair.sites:
					subprocess.call(["chair", "drop-site", site, "--force", "--no-backup", "--root-password", mariadb_password], cwd=chair_path)
				shutil.rmtree(chair_path, ignore_errors=True)

	def assert_folders(self, chair_name):
		for folder in paths_in_chair:
			self.assert_exists(chair_name, folder)
		self.assert_exists(chair_name, "apps", "vmraid")

	def assert_virtual_env(self, chair_name):
		chair_path = os.path.abspath(chair_name)
		python_path = os.path.abspath(os.path.join(chair_path, "env", "bin", "python"))
		self.assertTrue(python_path.startswith(chair_path))
		for subdir in ("bin", "lib", "share"):
			self.assert_exists(chair_name, "env", subdir)

	def assert_config(self, chair_name):
		for config, search_key in (
			("redis_queue.conf", "redis_queue.rdb"),
			("redis_socketio.conf", "redis_socketio.rdb"),
			("redis_cache.conf", "redis_cache.rdb")):

			self.assert_exists(chair_name, "config", config)

			with open(os.path.join(chair_name, "config", config), "r") as f:
				self.assertTrue(search_key in f.read())

	def assert_common_site_config(self, chair_name, expected_config):
		common_site_config_path = os.path.join(self.chaires_path, chair_name, 'sites', 'common_site_config.json')
		self.assertTrue(os.path.exists(common_site_config_path))

		with open(common_site_config_path, "r") as f:
			config = json.load(f)

		for key, value in list(expected_config.items()):
			self.assertEqual(config.get(key), value)

	def assert_exists(self, *args):
		self.assertTrue(os.path.exists(os.path.join(*args)))

	def new_site(self, site_name, chair_name):
		new_site_cmd = ["chair", "new-site", site_name, "--admin-password", "admin"]

		if os.environ.get('CI'):
			new_site_cmd.extend(["--mariadb-root-password", "travis"])

		subprocess.call(new_site_cmd, cwd=os.path.join(self.chaires_path, chair_name))

	def init_chair(self, chair_name, **kwargs):
		self.chaires.append(chair_name)
		vmraid_tmp_path = "/tmp/vmraid"

		if not os.path.exists(vmraid_tmp_path):
			exec_cmd(f"git clone https://github.com/vmraid/vmraid -b {VMRAID_BRANCH} --depth 1 --origin upstream {vmraid_tmp_path}")

		kwargs.update(dict(
			python=sys.executable,
			no_procfile=True,
			no_backups=True,
			vmraid_path=vmraid_tmp_path
		))

		if not os.path.exists(os.path.join(self.chaires_path, chair_name)):
			init(chair_name, **kwargs)
			exec_cmd("git remote set-url upstream https://github.com/vmraid/vmraid", cwd=os.path.join(self.chaires_path, chair_name, "apps", "vmraid"))

	def file_exists(self, path):
		if os.environ.get("CI"):
			return not subprocess.call(["sudo", "test", "-f", path])
		return os.path.isfile(path)

	def get_traceback(self):
		exc_type, exc_value, exc_tb = sys.exc_info()
		trace_list = traceback.format_exception(exc_type, exc_value, exc_tb)
		body = "".join(str(t) for t in trace_list)
		return body
