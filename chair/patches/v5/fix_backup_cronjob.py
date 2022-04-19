from chair.config.common_site_config import get_config
from crontab import CronTab


def execute(chair_path):
	"""
		This patch fixes a cron job that would backup sites every minute per 6 hours
	"""

	user = get_config(chair_path=chair_path).get('vmraid_user')
	user_crontab = CronTab(user=user)

	for job in user_crontab.find_comment("chair auto backups set for every 6 hours"):
		job.every(6).hours()
		user_crontab.write()
