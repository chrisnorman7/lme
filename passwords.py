"""Password functions."""

import string, options, logging, bcrypt
from builtins import range
from random import choice

logger = logging.getLogger('Passwords')

def to_password(value, salt = bcrypt.gensalt()):
 """Convert value to a hash with optional salt."""
 try:
  value = value.encode(options.args.default_encoding)
 except AttributeError:
  pass # Running on Python 3.
 try:
  salt = salt.encode(options.args.default_encoding)
 except AttributeError:
  pass # Running on Python 3.
 return bcrypt.hashpw(value, salt)

def check_password(guess, real):
 """Check guess against real."""
 guess = to_password(guess, real)
 return guess == bytes(real.encode(options.args.default_encoding) if hasattr(real, 'encode') else real) if type(guess) == bytes else real

def random_password(length = 8):
 """Generate a password constructed of random letters and numbers."""
 return ''.join(choice(string.digits + string.ascii_letters) for x in range(length))
