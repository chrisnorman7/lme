name = 'Little MUD Engine'
version = '0.1'
port = None # Should be set when initialise() is called.

import logging, errors, genders, options, util, objects, db, commands
from time import time, ctime
from socket import gethostbyaddr, gaierror
from threading import Thread

logger = logging.getLogger('Server')

started = time() # For the uptime command.

connections = {} # All active connections.

from twisted.protocols.basic import LineReceiver
from twisted.internet.protocol import ServerFactory
from twisted.internet import reactor
from twisted.internet.error import AlreadyCalled

# Possible connection states:
READY = 0 # The server will process commands normally.
USERNAME = 1 # The server is waiting for a login username.
PASSWORD = 2 # The server is waiting for a login password.
CREATE_USERNAME = 3 # The server is waiting for a username for a new character.
CREATE_PASSWORD_1 = 4 # The server is waiting for a new password.
CREATE_PASSWORD_2 = 5 # The server is waiting for the user to retype their password.
CREATE_NAME = 6 # The server is waiting for a new character name.
CREATE_SEX = 7 # The server is waiting for a sex to be chosen.
FROZEN = 8 # Input from this connection will be ignored until the state is changed.
READING = 9 # Waiting for the connected player to type something which will be passed to self.transport.read_func.

class ServerProtocol(LineReceiver):
 def do_timeout(self):
  """Actually disconnect the transport."""
  if not connections[self.transport]:
   self.sendLine(get_config('timeout_msg'), True)
   self.logger.info('Timed out.')
 
 def cancel_timeout(self):
  """Cancel the timeout for transport."""
  try:
   self.timeout.cancel()
  except (AttributeError, AlreadyCalled):
   pass # It's already dead.
  self.timeout = None
 
 def reset_timeout(self):
  if self.timeout:
   self.cancel_timeout()
  self.timeout = reactor.callLater(get_config('login_timeout'), self.do_timeout)
 
 def __init__(self, *args, **kwargs):
  self.state = USERNAME
  self.uid = None # The username which has been provided.
  self.pwd = None
  self.name = None
  self.timeout = None
  self.logger = logging.getLogger('<Connection unspecified>')
 
 def handle_line(self, line):
  """The threaded version of lineReceived."""
  if self.state == FROZEN:
   self.sendLine('You are totally frozen.')
   self.logger.info('attempted command while frozen: %s', line)
  elif self.state == READY:
   commands.do_command(connections[self.transport], line)
  else:
   self.reset_timeout()
   if self.state == USERNAME:
    if line:
     if line == 'new':
      self.create_username()
     else:
      self.uid = line
      self.state = PASSWORD
      self.sendLine('Password: ')
    else:
     self.sendLine('You must provide a username.', True)
   elif self.state == PASSWORD:
    for p in db.players:
     if p.authenticate(self.uid, line):
      logger.info('Authenticated as %s.', p.title())
      self.sendLine('Welcome back, {name}.{delimiter}{delimiter}You last logged in on {connect_time} from {connect_host}.'.format(name = p.title(), delimiter = self.delimiter.decode(options.args.default_encoding) if hasattr(self.delimiter, 'decode') else self.delimiter, connect_time = ctime(p.last_connected_time), connect_host = p.last_connected_host))
      self.post_login(p)
      break
    else:
     self.logger.info('Failed to authenticate with username: %s.', self.uid)
     self.sendLine('Invalid username and password combination.', True)
   elif self.state == CREATE_USERNAME:
    self.tries += 1
    if self.tries >= get_config('max_create_retries'):
     return self.sendLine(get_config('max_create_retries_exceeded'), True)
    if line:
     for p in db.players:
      if p.uid == line:
       self.sendLine('That username is already taken.')
       self.create_username()
       break
     else:
      self.uid = line
      self.tries = 0
      self.create_password()
    else:
     self.sendLine('Usernames must not be blank.', True)
   elif self.state == CREATE_PASSWORD_1:
    self.tries += 1
    if self.tries >= get_config('max_create_retries'):
     return self.sendLine(get_config('max_create_retries_exceeded'), True)
    if not line:
     self.sendLine('Passwords must not be blank.')
     self.create_password()
    else:
     self.sendLine('Retype password: ')
     self.tries = 0
     self.pwd = line
     self.state = CREATE_PASSWORD_2
   elif self.state == CREATE_PASSWORD_2:
    if line == self.pwd:
     self.tries = 0
     self.create_name()
    else:
     self.sendLine('Passwords do not match.')
     self.create_password()
   elif self.state == CREATE_NAME:
    self.tries += 1
    if self.tries >= get_config('max_create_retries'):
     return self.sendLine(get_config('max_create_retries_exceeded'), True)
    if line:
     line = line.title()
     for p in db.players:
      if p.name == line:
       self.sendLine('Sorry, but that name is already taken.')
       self.create_name()
     else:
      msg = util.disallowed_name(line)
      if msg:
       self.sendLine(msg)
       self.create_name()
      else:
       self.name = line
       self.tries = 0
       self.create_gender()
    else:
     self.sendLine('You must choose a name.')
     self.create_name()
   elif self.state == CREATE_SEX:
    if line == '1':
     gender = genders.MALE
    elif line == '2':
     gender = genders.FEMALE
    else:
     self.sendLine('Invalid input: %s. Try again.' % line)
     return self.create_gender()
    self.sendLine('You are now a %s.' % gender.sex)
    p = objects.PlayerObject(self.name)
    p.gender = gender
    p.uid = self.uid
    p.pwd = self.pwd
    if len(list(db.get_players())) == 1: # This is the only player.
     p.access = objects.players.WIZARD
     for o in db.objects:
      o.owner = p
    self.logger.info('Created %s player: %s.', 'wizard' if p.access else 'normal', p.title())
    p.move(db.objects_config['start_room'])
    self.post_login(p)
   elif self.state == READING:
    try:
     self.transport.read_func(line.decode(options.args.default_encoding) if hasattr(line, 'decode') else line)
    except Exception as e:
     self.sendLine('An error was raised while passing the line to the target function. See log for details.')
     self.logger.exception(e)
    finally:
     self.state = READY
     self.transport.read_func = None
   else:
    self.logger.warning('Unknown connection state: %s.', self.state)
    self.sendLine('Sorry, but an unknown error occurred. Please log in again.')
    if connections[self.transport]:
     connections[self.transport].transport = None
    connections[self.transport] = None
    self.get_username()
 
 def lineReceived(self, line):
  Thread(target = self.handle_line, args = [line.strip()]).start()
 
 def create_password(self):
  self.sendLine('New password')
  self.state = CREATE_PASSWORD_1
 
 def create_username(self):
  self.sendLine('Username to log in with: ')
  self.state = CREATE_USERNAME
 
 def create_name(self):
  self.sendLine('Enter a name for your new character: ')
  self.state = CREATE_NAME
 
 def create_gender(self):
  self.sendLine('Choose a sex for your new character:')
  for x, g in enumerate([genders.MALE, genders.FEMALE]):
   self.sendLine('[%s] %s.' % (x + 1, g.sex.title()))
  self.sendLine('Type a number: ')
  self.state = CREATE_SEX
 
 def post_login(self, object):
  self.tries = 0
  self.state = READY
  if object.transport:
   host, port = self.transport.getHost().host, self.transport.getHost().port
   self.logger.warning('Disconnecting in favour of %s:%s.', host, port)
   object.notify(get_config('redirect_msg').format(host = host, port = port), True)
   while object.transport:
    pass
  object.transport = self.transport
  connections[self.transport] = object
  object.last_connected_time = time()
  try:
   object.last_connected_host = gethostbyaddr(self.transport.hostname)[0]
  except gaierror:
   object.last_connected_host = self.transport.hostname
  object.notify(get_config('connect_msg'))
  object.on_connected()
 
 def get_username(self):
  self.state = USERNAME
  self.sendLine('Username (or new):')
 
 def connectionMade(self):
  self.logger.name = '<Connection %s:%s>' % (self.transport.getHost().host, self.transport.getHost().port)
  self.tries = 0
  connections[self.transport] = None
  if options.args.auto_login:
   for p in db.get_players():
    if p.uid == options.args.auto_login:
     self.logger.warning('Automatically authenticating as %s.', p.title())
     self.sendLine('Automatically authenticating you as %s.' % p.title())
     self.post_login(p)
     break
   else:
    self.logger.critical('Cannot find user %s in the database.', options.args.auto_login)
    self.sendLine('Sorry, autologin failed.', True)
  else:
   self.sendLine('Welcome to %s.' % get_config('server_name'))
   if options.args.max_connections and len(connections) > options.args.max_connections:
    self.sendLine('Sorry but the connection limit has been exceeded.', True)
    return self.logger.warning('Booting because connection limit exceeded.')
   elif db.players:
    self.get_username()
   else:
    self.sendLine('Creating initial user.')
    self.create_username()
   self.reset_timeout()
 
 def connectionLost(self, reason):
  if connections[self.transport]:
   connections[self.transport].on_disconnected()
   connections[self.transport].transport = None
  del connections[self.transport]
  self.logger.info('Disconnected: %s.', reason.getErrorMessage())
  self.cancel_timeout()
 
 def sendLine(self, line, disconnect = False):
  """Send a line to the client. If disconnect evaluates to True, also disconnect the client."""
  reactor.callFromThread(LineReceiver.sendLine, self, line.encode(options.args.default_encoding))
  if disconnect:
   reactor.callFromThread(self.transport.loseConnection)

class Factory(ServerFactory):
 def buildProtocol(self, addr):
  if addr.host in get_config('banned_hosts', []):
   return logger.warning('Blocked incoming connection from %s:%s.', addr.host, addr.port)
  else:
   logger.info('Incoming connection from %s:%s.', addr.host, addr.port)
   return ServerProtocol()

def disconnect_all():
 if connections:
  logger.info('Closing connections...')
  for transport in connections:
   transport.loseConnection()
 else:
  logger.info('No connections to close.')

def initialise():
 """Initialise the server."""
 logger.info('Max connections allowed: %s.', options.args.max_connections)
 reactor.addSystemEventTrigger('before', 'shutdown', disconnect_all)
 reactor.addSystemEventTrigger('after', 'shutdown', shutdown)
 port = reactor.listenTCP(options.args.port, Factory())
 logging.info('Now listening for connections on %s.', port.getHost())
 return port

def server_name():
 return '%s (version %s)' % (get_config('server_name'), version)

def uptime():
 """Returns the number of seconds the server has been up for."""
 return time() - started

def shutdown():
 db.dump()
 logging.info('Server shutting down.')

def get_config(key, default = KeyError):
 if default == KeyError:
  return db.server_config[key]
 else:
  return db.server_config.get(key, default)

def set_config(key, value):
 logger.debug('Server_config[%s] = %s.', key, value)
 db.server_config[key] = value

def clear_config(key):
 del db.server_config[key]
