from chair.config.common_site_config import update_config


def execute(chair_path):
	update_config({'live_reload': True}, chair_path)
