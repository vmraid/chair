VERSION = "5.0.0-dev"
PROJECT_NAME = "vmraid-chair"
VMRAID_VERSION = None
current_path = None
updated_path = None
LOG_BUFFER = []


def set_vmraid_version(chair_path="."):
	from .utils.app import get_current_vmraid_version

	global VMRAID_VERSION
	if not VMRAID_VERSION:
		VMRAID_VERSION = get_current_vmraid_version(chair_path=chair_path)
