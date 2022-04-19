# imports - standard imports
import getpass
import os

# imports - third partyimports
import click

# imports - module imports
import chair
from chair.app import use_rq
from chair.chair import Chair
from chair.config.common_site_config import get_gunicorn_workers, update_config
from chair.utils import exec_cmd, which, get_chair_name


def generate_systemd_config(chair_path, user=None, yes=False,
	stop=False, create_symlinks=False,
	delete_symlinks=False):

	if not user:
		user = getpass.getuser()

	config = Chair(chair_path).conf

	chair_dir = os.path.abspath(chair_path)
	chair_name = get_chair_name(chair_path)

	if stop:
		exec_cmd(f'sudo systemctl stop -- $(systemctl show -p Requires {chair_name}.target | cut -d= -f2)')
		return

	if create_symlinks:
		_create_symlinks(chair_path)
		return

	if delete_symlinks:
		_delete_symlinks(chair_path)
		return

	number_of_workers = config.get('background_workers') or 1
	background_workers = []
	for i in range(number_of_workers):
		background_workers.append(get_chair_name(chair_path) + "-vmraid-default-worker@" + str(i+1) + ".service")

	for i in range(number_of_workers):
		background_workers.append(get_chair_name(chair_path) + "-vmraid-short-worker@" + str(i+1) + ".service")

	for i in range(number_of_workers):
		background_workers.append(get_chair_name(chair_path) + "-vmraid-long-worker@" + str(i+1) + ".service")

	chair_info = {
		"chair_dir": chair_dir,
		"sites_dir": os.path.join(chair_dir, 'sites'),
		"user": user,
		"use_rq": use_rq(chair_path),
		"http_timeout": config.get("http_timeout", 120),
		"redis_server": which('redis-server'),
		"node": which('node') or which('nodejs'),
		"redis_cache_config": os.path.join(chair_dir, 'config', 'redis_cache.conf'),
		"redis_socketio_config": os.path.join(chair_dir, 'config', 'redis_socketio.conf'),
		"redis_queue_config": os.path.join(chair_dir, 'config', 'redis_queue.conf'),
		"webserver_port": config.get('webserver_port', 8000),
		"gunicorn_workers": config.get('gunicorn_workers', get_gunicorn_workers()["gunicorn_workers"]),
		"chair_name": get_chair_name(chair_path),
		"worker_target_wants": " ".join(background_workers),
		"chair_cmd": which('chair')
	}

	if not yes:
		click.confirm('current systemd configuration will be overwritten. Do you want to continue?',
			abort=True)

	setup_systemd_directory(chair_path)
	setup_main_config(chair_info, chair_path)
	setup_workers_config(chair_info, chair_path)
	setup_web_config(chair_info, chair_path)
	setup_redis_config(chair_info, chair_path)

	update_config({'restart_systemd_on_update': True}, chair_path=chair_path)
	update_config({'restart_supervisor_on_update': False}, chair_path=chair_path)

def setup_systemd_directory(chair_path):
	if not os.path.exists(os.path.join(chair_path, 'config', 'systemd')):
		os.makedirs(os.path.join(chair_path, 'config', 'systemd'))

def setup_main_config(chair_info, chair_path):
	# Main config
	chair_template = chair.config.env().get_template('systemd/vmraid-chair.target')
	chair_config = chair_template.render(**chair_info)
	chair_config_path = os.path.join(chair_path, 'config', 'systemd' , chair_info.get("chair_name") + '.target')

	with open(chair_config_path, 'w') as f:
		f.write(chair_config)

def setup_workers_config(chair_info, chair_path):
	# Worker Group
	chair_workers_target_template = chair.config.env().get_template('systemd/vmraid-chair-workers.target')
	chair_default_worker_template = chair.config.env().get_template('systemd/vmraid-chair-vmraid-default-worker.service')
	chair_short_worker_template = chair.config.env().get_template('systemd/vmraid-chair-vmraid-short-worker.service')
	chair_long_worker_template = chair.config.env().get_template('systemd/vmraid-chair-vmraid-long-worker.service')
	chair_schedule_worker_template = chair.config.env().get_template('systemd/vmraid-chair-vmraid-schedule.service')

	chair_workers_target_config = chair_workers_target_template.render(**chair_info)
	chair_default_worker_config = chair_default_worker_template.render(**chair_info)
	chair_short_worker_config = chair_short_worker_template.render(**chair_info)
	chair_long_worker_config = chair_long_worker_template.render(**chair_info)
	chair_schedule_worker_config = chair_schedule_worker_template.render(**chair_info)

	chair_workers_target_config_path = os.path.join(chair_path, 'config', 'systemd' , chair_info.get("chair_name") + '-workers.target')
	chair_default_worker_config_path = os.path.join(chair_path, 'config', 'systemd' , chair_info.get("chair_name") + '-vmraid-default-worker@.service')
	chair_short_worker_config_path = os.path.join(chair_path, 'config', 'systemd' , chair_info.get("chair_name") + '-vmraid-short-worker@.service')
	chair_long_worker_config_path = os.path.join(chair_path, 'config', 'systemd' , chair_info.get("chair_name") + '-vmraid-long-worker@.service')
	chair_schedule_worker_config_path = os.path.join(chair_path, 'config', 'systemd' , chair_info.get("chair_name") + '-vmraid-schedule.service')

	with open(chair_workers_target_config_path, 'w') as f:
		f.write(chair_workers_target_config)

	with open(chair_default_worker_config_path, 'w') as f:
		f.write(chair_default_worker_config)

	with open(chair_short_worker_config_path, 'w') as f:
		f.write(chair_short_worker_config)

	with open(chair_long_worker_config_path, 'w') as f:
		f.write(chair_long_worker_config)

	with open(chair_schedule_worker_config_path, 'w') as f:
		f.write(chair_schedule_worker_config)

def setup_web_config(chair_info, chair_path):
	# Web Group
	chair_web_target_template = chair.config.env().get_template('systemd/vmraid-chair-web.target')
	chair_web_service_template = chair.config.env().get_template('systemd/vmraid-chair-vmraid-web.service')
	chair_node_socketio_template = chair.config.env().get_template('systemd/vmraid-chair-node-socketio.service')

	chair_web_target_config = chair_web_target_template.render(**chair_info)
	chair_web_service_config = chair_web_service_template.render(**chair_info)
	chair_node_socketio_config = chair_node_socketio_template.render(**chair_info)

	chair_web_target_config_path = os.path.join(chair_path, 'config', 'systemd' , chair_info.get("chair_name") + '-web.target')
	chair_web_service_config_path = os.path.join(chair_path, 'config', 'systemd' , chair_info.get("chair_name") + '-vmraid-web.service')
	chair_node_socketio_config_path = os.path.join(chair_path, 'config', 'systemd' , chair_info.get("chair_name") + '-node-socketio.service')

	with open(chair_web_target_config_path, 'w') as f:
		f.write(chair_web_target_config)

	with open(chair_web_service_config_path, 'w') as f:
		f.write(chair_web_service_config)

	with open(chair_node_socketio_config_path, 'w') as f:
		f.write(chair_node_socketio_config)

def setup_redis_config(chair_info, chair_path):
	# Redis Group
	chair_redis_target_template = chair.config.env().get_template('systemd/vmraid-chair-redis.target')
	chair_redis_cache_template = chair.config.env().get_template('systemd/vmraid-chair-redis-cache.service')
	chair_redis_queue_template = chair.config.env().get_template('systemd/vmraid-chair-redis-queue.service')
	chair_redis_socketio_template = chair.config.env().get_template('systemd/vmraid-chair-redis-socketio.service')

	chair_redis_target_config = chair_redis_target_template.render(**chair_info)
	chair_redis_cache_config = chair_redis_cache_template.render(**chair_info)
	chair_redis_queue_config = chair_redis_queue_template.render(**chair_info)
	chair_redis_socketio_config = chair_redis_socketio_template.render(**chair_info)

	chair_redis_target_config_path = os.path.join(chair_path, 'config', 'systemd' , chair_info.get("chair_name") + '-redis.target')
	chair_redis_cache_config_path = os.path.join(chair_path, 'config', 'systemd' , chair_info.get("chair_name") + '-redis-cache.service')
	chair_redis_queue_config_path = os.path.join(chair_path, 'config', 'systemd' , chair_info.get("chair_name") + '-redis-queue.service')
	chair_redis_socketio_config_path = os.path.join(chair_path, 'config', 'systemd' , chair_info.get("chair_name") + '-redis-socketio.service')

	with open(chair_redis_target_config_path, 'w') as f:
		f.write(chair_redis_target_config)

	with open(chair_redis_cache_config_path, 'w') as f:
		f.write(chair_redis_cache_config)

	with open(chair_redis_queue_config_path, 'w') as f:
		f.write(chair_redis_queue_config)

	with open(chair_redis_socketio_config_path, 'w') as f:
		f.write(chair_redis_socketio_config)

def _create_symlinks(chair_path):
	chair_dir = os.path.abspath(chair_path)
	etc_systemd_system = os.path.join('/', 'etc', 'systemd', 'system')
	config_path = os.path.join(chair_dir, 'config', 'systemd')
	unit_files = get_unit_files(chair_dir)
	for unit_file in unit_files:
		filename = "".join(unit_file)
		exec_cmd(f'sudo ln -s {config_path}/{filename} {etc_systemd_system}/{"".join(unit_file)}')
	exec_cmd('sudo systemctl daemon-reload')

def _delete_symlinks(chair_path):
	chair_dir = os.path.abspath(chair_path)
	etc_systemd_system = os.path.join('/', 'etc', 'systemd', 'system')
	unit_files = get_unit_files(chair_dir)
	for unit_file in unit_files:
		exec_cmd(f'sudo rm {etc_systemd_system}/{"".join(unit_file)}')
	exec_cmd('sudo systemctl daemon-reload')

def get_unit_files(chair_path):
	chair_name = get_chair_name(chair_path)
	unit_files = [
		[chair_name, ".target"],
		[chair_name+"-workers", ".target"],
		[chair_name+"-web", ".target"],
		[chair_name+"-redis", ".target"],
		[chair_name+"-vmraid-default-worker@", ".service"],
		[chair_name+"-vmraid-short-worker@", ".service"],
		[chair_name+"-vmraid-long-worker@", ".service"],
		[chair_name+"-vmraid-schedule", ".service"],
		[chair_name+"-vmraid-web", ".service"],
		[chair_name+"-node-socketio", ".service"],
		[chair_name+"-redis-cache", ".service"],
		[chair_name+"-redis-queue", ".service"],
		[chair_name+"-redis-socketio", ".service"],
	]
	return unit_files
