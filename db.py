"""Database routines and storage."""

objects = [] # List of all loaded objects in the game.
players = [] # List of created players.

server_config = dict( # Server configuration.
 connect_msg = '*** Connected ***',
 login_timeout = 60, # Number of seconds to wait before disconnecting unlogged in connections.
 timeout_msg = '*** Timed out while waiting for login. ***',
 disconnect_msg = '*** Disconnected ***',
 redirect_msg = '*** Redirecting to {host}:{port}. ***',
 max_create_retries = 5,
 max_create_retries_exceeded = 'Maximum number of retries exceeded. Please come again.',
 server_name = 'The LittleMUD Test Server',
 command_history_length = 100, # The number of commands to store for a given player.
 banned_hosts = [], # Hosts which aren't allowed to connect.
)

objects_config = {} # Configuration which requires objects.

import json, logging, objects as _objects, server, options
logging.basicConfig(level = 'INFO')
logger = logging.getLogger('DB')

def dump_object_property(p):
 """Return objects into integers which can be reladed later."""
 if type(p) == dict:
  stuff = {}
  for x, y in p.items():
   stuff[x] = dump_object_property(y)
 elif type(p) == list:
  stuff = []
  for x in p:
   stuff.append(dump_object_property(x))
 elif isinstance(p, _objects.BaseObject):
  stuff = objects.index(p)
 else:
  stuff = p
 return stuff

def load_object_property(p):
 """Transform dumped objects into real ones."""
 if type(p) == dict:
  stuff = {}
  for x, y in p.items():
   stuff[x] = load_object_property(y)
 elif type(p) == list:
  stuff = []
  for x in p:
   stuff.append(load_object_property(x))
 elif type(p) == int:
  stuff = objects[p]
 else:
  stuff = p
 return stuff

def load(filename = None):
 """Load the database from the file object fp."""
 if filename == None:
  filename = options.args.dump_file
 logger.info('Loading database from %s.', filename)
 properties = []
 with open(filename, 'r') as f:
  stuff = json.load(f)
  o = stuff.get('objects', [])
  server_config.update(**stuff.get('server_config', {}))
  for x, y in o:
   new = getattr(_objects, x)()
   y['object'] = new
   properties.append(y)
  for p in properties:
   p['object'].load(p)
  for x, y in stuff.get('objects_config', {}).items():
   objects_config[x] = load_object_property(y)
  if 'start_room' not in objects_config:
   logging.info('Creating start room.')
   objects_config['start_room'] = _objects.RoomObject('The First Room')
  else:
   logging.info('Start room: %s.', objects_config['start_room'])
  logger.info('Loaded %s object%s.', len(properties), '' if len(properties) == 1 else 's')

def dump(filename = None):
 """Dump a serialised version of the current object state to fp."""
 if filename == None:
  filename = options.args.dump_file
 stuff = dict(
  objects = [x.dump() for x in objects],
  server_config = server_config,
  objects_config = dump_object_property(objects_config),
 )
 logger.info('Dumping the database to %s.', filename)
 with open(filename, 'w') as f:
  json.dump(stuff, f, indent = 1)
  logger.info('Dumped %s object%s.', len(stuff['objects']), '' if len(stuff['objects']) == 1 else 's')

def clear():
 while objects:
  objects[0].destroy()

def get_players():
 """Return a list of players."""
 for o in objects:
  if isinstance(o, _objects.PlayerObject):
   yield o

def notify_players(text, access = 0):
 """Send text to all players who have an access level >= access."""
 for p in get_players():
  if p.access >= access:
   p.notify(text)
