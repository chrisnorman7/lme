class BaseError(Exception):
 """Base error."""
 def __init__(self, message = None):
  super(BaseError, self).__init__(self.__doc__ if message == None else message)

class ContainmentError(BaseError):
 """Objects cannot be moved into themselves or into objects which contain them."""

class PermissionsError(BaseError):
 """You do not have permission to perform that action."""

class NoClueError(BaseError):
 """Something terrible happened."""
