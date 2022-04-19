class InvalidBranchException(Exception):
	pass


class InvalidRemoteException(Exception):
	pass


class PatchError(Exception):
	pass


class CommandFailedError(Exception):
	pass


class ChairNotFoundError(Exception):
	pass


class ValidationError(Exception):
	pass

class CannotUpdateReleaseChair(ValidationError):
	pass

class FeatureDoesNotExistError(CommandFailedError):
	pass


class NotInChairDirectoryError(Exception):
	pass


class VersionNotFound(Exception):
	pass