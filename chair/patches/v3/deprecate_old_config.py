import os, json
from chair.config.common_site_config import get_config, put_config, get_common_site_config

def execute(chair_path):
	# deprecate chair config
	chair_config_path = os.path.join(chair_path, 'config.json')
	if not os.path.exists(chair_config_path):
		return

	with open(chair_config_path, "r") as f:
		chair_config = json.loads(f.read())

	common_site_config = get_common_site_config(chair_path)
	common_site_config.update(chair_config)
	put_config(common_site_config, chair_path)

	# remove chair/config.json
	os.remove(chair_config_path)

	# change keys
	config = get_config(chair_path)
	changed = False
	for from_key, to_key, default in (
			("celery_broker", "redis_queue", "redis://localhost:6379"),
			("async_redis_server", "redis_socketio", "redis://localhost:12311"),
			("cache_redis_server", "redis_cache", "redis://localhost:11311")
		):
		if from_key in config:
			config[to_key] = config[from_key]
			del config[from_key]
			changed = True

		elif to_key not in config:
			config[to_key] = default
			changed = True

	if changed:
		put_config(config, chair_path)
