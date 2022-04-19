# imports - standard imports
import getpass
import os
import subprocess

# imports - module imports
from chair.cli import change_uid_msg
from chair.config.production_setup import get_supervisor_confdir, is_centos7, service
from chair.config.common_site_config import get_config
from chair.utils import exec_cmd, get_chair_name, get_cmd_output


def is_sudoers_set():
	"""Check if chair sudoers is set"""
	cmd = ["sudo", "-n", "chair"]

	with open(os.devnull, "wb") as f:
		return_code_check = not subprocess.call(cmd, stdout=f)

	if return_code_check:
		try:
			chair_warn = change_uid_msg in get_cmd_output(cmd, _raise=False)
		except subprocess.CalledProcessError:
			chair_warn = False
		finally:
			return_code_check = return_code_check and chair_warn

	return return_code_check


def is_production_set(chair_path):
	"""Check if production is set for current chair"""
	production_setup = False
	chair_name = get_chair_name(chair_path)

	supervisor_conf_extn = "ini" if is_centos7() else "conf"
	supervisor_conf_file_name = f'{chair_name}.{supervisor_conf_extn}'
	supervisor_conf = os.path.join(get_supervisor_confdir(), supervisor_conf_file_name)

	if os.path.exists(supervisor_conf):
		production_setup = production_setup or True

	nginx_conf = f'/etc/nginx/conf.d/{chair_name}.conf'

	if os.path.exists(nginx_conf):
		production_setup = production_setup or True

	return production_setup


def execute(chair_path):
	"""This patch checks if chair sudoers is set and regenerate supervisor and sudoers files"""
	user = get_config('.').get("vmraid_user") or getpass.getuser()

	if is_sudoers_set():
		if is_production_set(chair_path):
			exec_cmd(f"sudo chair setup supervisor --yes --user {user}")
			service("supervisord", "restart")

		exec_cmd(f"sudo chair setup sudoers {user}")
