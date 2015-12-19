"""Lump objects."""

from errors import ContainmentError, PermissionsError

NOWHERE = None
NOONE = None
NOTHING = None
NOTHINGSPECIAL = 'You see nothing special.'

import logging, db

logger = logging.getLogger('Base Objects')

class BaseObject(object):
 @property
 def description(self):
  return self._description or NOTHINGSPECIAL
 
 @description.setter
 def description(self, value):
  self._description = value
 
 @property
 def contents(self):
  return self._contents
 
 @contents.setter
 def contents(self, value):
  self._contents = value
 
 def __init__(self,
  name = 'Untitled Object',
  description = '',
  drop_msg = 'You drop {name}.',
  take_msg = 'You take {name}.',
  odrop_msg = '{player_title} drops {name}.',
  otake_msg = '{player_title} takes {name}.'
 ):
  self.dump_properties = [
   'name',
   '_description',
   'drop_msg',
   'take_msg',
   'odrop_msg',
   'otake_msg',
   'help',
  ]
  self.dump_object_properties = [
   'location',
   'contents',
   'owner',
  ]
  self.name = name # The name of this object.
  self._description = description
  self._contents = [] # The stuff that resides in this object.
  self.help = None
  self.owner = self
  self.drop_msg = drop_msg
  self.take_msg = take_msg
  self.odrop_msg = odrop_msg
  self.otake_msg = otake_msg
  self.location = NOWHERE # Where this object resides.
  logger.debug('Created object %s.', self.name)
  db.objects.append(self)
 
 def title(self):
  """Return a prettier version of name."""
  return self.name
 
 def locations(self):
  """Return a list of all the enclosed locations for this object."""
  l = self.location
  while l != NOWHERE:
   yield l
   l = l.location
 
 def notify(self, text):
  """Used to notify this object of something. Return True if something was actually done."""
  return False
 
 def move(self, obj):
  """Used to move this object to another location."""
  l = self.location
  if l == obj:
   logger.debug('Not bothering to move object %s to same location.', self)
  elif obj == self or obj in self.locations():
   raise ContainmentError
  elif l == NOWHERE or l.on_exit(self):
   logger.debug('Object %s allowed to exit %s.', self, l)
   if obj == NOWHERE or obj.on_enter(self):
    logger.debug('Entry to %s allowed.', obj)
    self.location = obj
   elif l == NOWHERE or l.on_enter(self):
    logger.debug('Entry to %s failed, falling back on old location.', obj)
    self.location = l
   else:
    logger.warning('Cannot enter %s or old location %s. Falling back to %s.', obj, l, NOWHERE)
    self.location = NOWHERE
  else:
   logger.debug('Object %s not allowed to exit %s.', self, l)
 
 def on_enter(self, obj):
  """Called when an object obj wishes to enter this object. Should return True if the entry is permitted and self.contents is updated propertly."""
  logger.debug('Allowing %s into %s.', obj, self)
  if obj not in self.contents:
   self.contents.append(obj)
  return True
 
 def on_exit(self, obj):
  """Called when an object obj wishes to exit this object. Should return True if the move is allowed and self.contents is updated properly."""
  logger.debug('Allowing object %s to exit %s.', obj, self)
  if obj in self.contents:
   self.contents.remove(obj)
  return True
 
 def format_message(self, msg, player = NOONE):
  return messages.format_message(msg, object = self, location = self.location, player = player)
 
 def destroy(self):
  """Destroy this object and remove it from the game."""
  if self.location != NOWHERE:
   try:
    self.location.contents.remove(self)
   except IndexError:
    pass
  try:
   db.objects.remove(self)
  except ValueError:
   pass # It's already gone.
  logger.info('Object %s destroyed.', self)
 
 def format_message(
  self,
  msg,
  object = False,
  location = False,
  player = NOONE
 ):
  """Format a message for this object."""
  if object == False:
   object = self
  if location == False:
   location = self.location
  return msg.format(
   player_name = 'noone' if player == NOONE else player.name,
   player_title = 'Noone' if player == NOONE else player.title(),
   name = 'nothing' if object == NOTHING else object.name,
   title = 'Nothing' if object == NOTHING else object.title(),
   location_name = 'nowhere' if location == NOWHERE else object.location.name,
   location_title = 'Nowhere' if location == NOWHERE else object.location.title()
  )
 
 def notify_message(self, *args, **kwargs):
  """Notify this object with a formatted message."""
  self.notify(self, self.format_message(*args, **kwargs))
 
 def dump(self):
  """Return a tuple containing information necessary to reconstruct this object. Used with db.dump."""
  stuff = {}
  stuff['properties'] = {}
  for p in self.dump_properties:
   stuff['properties'][p] = getattr(self, p)
  stuff['object_properties'] = {}
  for p in self.dump_object_properties:
   stuff['object_properties'][p] = db.dump_object_property(getattr(self, p))
  return [self.__class__.__name__, stuff]
 
 def load(self, stuff):
  """Merge the data in stuff onto this object."""
  for x, y in stuff.get('properties', {}).items():
   try:
    setattr(self, x, y)
   except Exception as e:
    logger.warning('Could not set property %s = %s.', x, y)
    logger.exception(e)
  for x, y in stuff.get('object_properties').items():
   try:
    setattr(self, x, db.load_object_property(y))
   except Exception as e:
    logger.warning('Unable to set object property %s = %s.', x, y)
    logger.exception(e)
 
 def __str__(self):
  return '<%s:(%s)>' % (self.__class__.__name__, self.name)
 
 def __repr__(self):
  return '<%s:(name=%s, location=%s)' % (self.__class__.__name__, self.name, str(self.location))

from .mobs import MobObject
from .players import PlayerObject
from .rooms import RoomObject
from .zones import ZoneObject
