name = 'LittleMUD Server'
version = '0.1'

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
 def __init__(self, *args, **kwargs):
  self.state = USERNAME
  self.uid = None # The username which has been provided.
  self.pwd = None
  self.name = None
 
 def handle_line(self, line):
  """The threaded version of lineReceived."""
  if self.state == FROZEN:
   self.sendLine('You are totally frozen.')
   logger.info('%s attempted command while frozen: %s', line)
  elif self.state == READY:
   commands.do_command(connections[self.transport], line)
  elif self.state == USERNAME:
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
     logger.info('%s authenticated as %s.', self.transport.hostname, p.title())
     self.sendLine('Welcome back, {name}.{delimiter}{delimiter}You last logged in on {connect_time} from {connect_host}.'.format(name = p.title(), delimiter = self.delimiter, connect_time = ctime(p.last_connected_time), connect_host = p.last_connected_host))
     self.post_login(p)
     break
   else:
    logger.info('%s failed to authenticate with username: %s.', self.transport.hostname, self.uid)
    self.sendLine('Invalid username and password combination.', True)
  elif self.state == CREATE_USERNAME:
   self.tries += 1
   if self.tries >= db.server_config['max_create_retries']:
    return self.sendLine(db.server_config['max_create_retries_exceeded'], True)
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
   if self.tries >= db.server_config['max_create_retries']:
    return self.sendLine(db.server_config['max_create_retries_exceeded'], True)
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
   if self.tries >= db.server_config['max_create_retries']:
    return self.sendLine(db.server_config['max_create_retries_exceeded'], True)
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
   logger.info('%s created %s player: %s.', self.transport.hostname, 'wizard' if p.access else 'normal', p.title())
   p.move(db.objects_config['start_room'])
   self.post_login(p)
  elif self.state == READING:
   try:
    self.transport.read_func(line)
   except Exception as e:
    self.transport.write('An error was raised while passing the line to the target function. See log for details.\r\n'.encode(options.args.default_encoding))
    logging.critical('While trying to read a line from host %s the following error was raised:', self.transport.host)
    logger.exception(e)
  else:
   logger.warning('Unknown connection state: %s.', self.state)
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
   logger.warning('Disconnecting %s:%s in favour of %s:%s.', object.transport.getHost().host, object.transport.getHost().port, host, port)
   object.notify(db.server_config['redirect_msg'].format(host = host, port = port), True)
   while object.transport:
    pass
  object.transport = self.transport
  connections[self.transport] = object
  object.last_connected_time = time()
  try:
   object.last_connected_host = gethostbyaddr(self.transport.hostname)[0]
  except gaierror:
   object.last_connected_host = self.transport.hostname
  object.notify(db.server_config['connect_msg'])
  object.on_connected()
 
 def get_username(self):
  self.state = USERNAME
  self.sendLine('Username (or new):')
 
 def connectionMade(self):
  self.tries = 0
  connections[self.transport] = None
  self.sendLine('Welcome to %s.' % db.server_config['server_name'])
  if db.players:
   self.get_username()
  else:
   self.sendLine('Creating initial user.')
   self.create_username()
 
 def connectionLost(self, reason):
  if connections[self.transport]:
   connections[self.transport].on_disconnected()
   connections[self.transport].transport = None
  del connections[self.transport]
  logger.info('%s disconnected: %s.', self.transport.hostname, reason.getErrorMessage())
 
 def sendLine(self, line, disconnect = False):
  """Send a line to the client. If disconnect evaluates to True, also disconnect the client."""
  reactor.callFromThread(LineReceiver.sendLine, self, line.encode(options.args.default_encoding))
  if disconnect:
   reactor.callFromThread(self.transport.loseConnection)

class Factory(ServerFactory):
 def buildProtocol(self, addr):
  if addr.host in db.server_config.get('banned_hosts', []):
   return logger.warning('Blocked incoming connection from %s:%s.', addr.host, addr.port)
  else:
   logger.info('Incoming connection from %s:%s.', addr.host, addr.port)
   return ServerProtocol()

def disconnect_all():
 if connections:
  logger.info('Closing connections...')
  for transport in connections:
   transport.abortConnection()
 else:
  logger.info('No connections to close.')

def initialise():
 """Initialise the server."""
 reactor.listenTCP(options.args.port, Factory())
 logger.info('Listening for connections on port %s.', options.args.port)
 reactor.addSystemEventTrigger('before', 'shutdown', disconnect_all)

def server_name():
 return '%s (version %s)' % (name, version)

def uptime():
 """Returns the number of seconds the server has been up for."""
 return time() - started