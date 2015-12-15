"""Player """

import db, logging, passwords, util, options, server
from objects import *
from twisted.internet import reactor

logger = logging.getLogger('Player Objects')

# Access permissions
NORMAL = 0 # Standard player.
BUILDER = 1 # Player can build.
PROGRAMMER = 2 # Player can program and eval code.
WIZARD = 3 # Player can do anything.

class PlayerObject(MobObject):
 @property
 def pwd(self):
  return self._pwd
 
 @pwd.setter
 def pwd(self, value):
  self._pwd = passwords.to_password(value)
  logger.info('Changed password for %s.', self)
 
 def __init__(self, *args, **kwargs):
  super(PlayerObject, self).__init__(*args, **kwargs)
  self.last_command_time = 0.0 # The last time this object executed a command.
  self.dump_properties += [
   'banned',
   'uid',
   '_pwd',
   'last_connected_time',
   'last_connected_host',
   'access'
  ]
  self.access = NORMAL
  self.last_connected_time = None
  self.last_connected_host = None
  self.banned = False # If True disallow the player from logging in.
  self.uid = '' # The username to log in with.
  self._pwd = '' # The password to log in with.
  self.transport = None # The transport to write data to.
  db.players.append(self)
 
 def authenticate(self, uid, pwd):
  return bytes(uid.encode(options.args.default_encoding) if type(uid) != bytes else uid) == self.uid.encode(options.args.default_encoding) and passwords.check_password(pwd, self.pwd)
 
 def on_connected(self):
  """Called when this character connects."""
  self.do_look()

 def on_disconnected(self):
  """Called when this player disconnects."""
  pass
 
 def is_connected(self):
  """Returns True or False depending on whether this object is connected or not."""
  if self.transport:
   return True
  else:
   return False
 
 def do_look(self, thing = False):
  """Look at thing."""
  if thing == False:
   thing = self.location
  if thing in [NOTHING, NOWHERE, NOONE]:
   return self.notify(NOTHINGSPECIAL)
  else:
   self.notify(thing.title())
   self.notify(thing.description)
 
 def notify(self, text):
  if self.transport:
   s = '%s\r\n' % text
   reactor.callFromThread(self.transport.write, util.format_colour(s).encode('utf-8') )
   return True
  else:
   return False
 
 def read(self, func, text = None):
  """Read a line of input from a player."""
  if text:
   self.notify(text)
  self.transport.read_func = func
  self.transport.protocol.state = server.READING
