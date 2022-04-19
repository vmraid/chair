import os
import shutil
import subprocess
import unittest
from tabnanny import check

from chair.app import App
from chair.chair import Chair
from chair.exceptions import InvalidRemoteException
from chair.utils import is_valid_vmraid_branch


class TestUtils(unittest.TestCase):
	def test_app_utils(self):
		git_url = "https://github.com/vmraid/vmraid"
		branch = "develop"
		app = App(name=git_url, branch=branch, chair=Chair("."))
		self.assertTrue(
			all(
				[
					app.name == git_url,
					app.branch == branch,
					app.tag == branch,
					app.is_url == True,
					app.on_disk == False,
					app.org == "vmraid",
					app.url == git_url,
				]
			)
		)

	def test_is_valid_vmraid_branch(self):
		with self.assertRaises(InvalidRemoteException):
			is_valid_vmraid_branch("https://github.com/vmraid/vmraid.git", vmraid_branch="random-branch")
			is_valid_vmraid_branch("https://github.com/random/random.git", vmraid_branch="random-branch")

		is_valid_vmraid_branch("https://github.com/vmraid/vmraid.git", vmraid_branch="develop")

	def test_app_states(self):
		chair_dir = "./sandbox"
		sites_dir = os.path.join(chair_dir, "sites")

		if not os.path.exists(sites_dir):
			os.makedirs(sites_dir)

		fake_chair = Chair(chair_dir)

		self.assertTrue(hasattr(fake_chair.apps, "states"))

		fake_chair.apps.states = {
			"vmraid": {"resolution": {"branch": "develop", "commit_hash": "234rwefd"}, "version": "14.0.0-dev"}
		}
		fake_chair.apps.update_apps_states()

		self.assertEqual(fake_chair.apps.states, {})

		vmraid_path = os.path.join(chair_dir, "apps", "vmraid")

		os.makedirs(os.path.join(vmraid_path, "vmraid"))

		subprocess.run(["git", "init"], cwd=vmraid_path, capture_output=True, check=True)

		with open(os.path.join(vmraid_path, "vmraid", "__init__.py"), "w+") as f:
			f.write("__version__ = '11.0'")

		subprocess.run(["git", "add", "."], cwd=vmraid_path, capture_output=True, check=True)
		subprocess.run(["git", "commit", "-m", "temp"], cwd=vmraid_path, capture_output=True, check=True)

		fake_chair.apps.update_apps_states("vmraid")

		self.assertIn("vmraid", fake_chair.apps.states)
		self.assertIn("version", fake_chair.apps.states["vmraid"])
		self.assertEqual("11.0", fake_chair.apps.states["vmraid"]["version"])

		shutil.rmtree(chair_dir)

	def test_get_dependencies(self):
		git_url = "https://github.com/vmraid/healthcare"
		branch = "develop"
		fake_app = App(git_url, branch=branch)
		self.assertIn("erpadda", fake_app._get_dependencies())
		git_url = git_url.replace("healthcare", "erpadda")
		fake_app = App(git_url)
		self.assertTrue(len(fake_app._get_dependencies()) == 0)
