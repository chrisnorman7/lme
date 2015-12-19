"""Room objects."""

import logging, objects

logger = logging.getLogger('Room Objects')

class ExtraObject(objects.BaseObject):
 pass

class RoomObject(objects.BaseObject):
 """A room object. This is the main scenery for the game."""
 @property
 def description(self):
  if self.is_light():
   return self._description or objects.NOTHINGSPECIAL
  else:
   return self.dark_msg
 
 @description.setter
 def description(self, value):
  self._description = value
 
 def __init__(self, *args, **kwargs):
  super(RoomObject, self).__init__(*args, **kwargs)
  self.dump_properties += [
   'safe',
   'light',
   'floor_type',
   'dark_msg',
  ]
  self.dump_object_properties += [
   'exits',
   'entrances',
   'extras',
  ]
  self.safe = False # If True, fighting is impossible in this room.
  self.light = True # If False, this room is always dark.
  self.floor_type = 1 # The type of floor.
  self.dark_msg = 'It is too dark to see.' # The message which is shown when someone tries to look without light.
  self.exits = [] # The exits from this room.
  self.entrances = [] # The entrances to this room.
  self.extras = [] # The extra things to look at.
 
 def is_light(self):
  """Return True if this room should be lit."""
  return self.light
 
 def is_safe(self):
  """Return True if this room is safe."""
  return self.is_safe
 
 def add_extra(self, name, text):
  """Add an extra to the room."""
  extra = ExtraObject(name, text)
  self.extras.append(extra)
  return extra
 
 def remove_extra(self, extra):
  """Remove the extra from the room."""
  self.extras.remove(extra)
 
 def announce(self, text, player):
  """Announce to every object in the room other than player."""
  return self.announce_all_but([player], text)
 
 def announce_all(self, text):
  """Announce something to every object in the room."""
  return self.announce_all_but([], text)
 
 def announce_all_but(self, objects, text):
  """Announce text to every object which isn't in objects list."""
  for c in self.contents:
   if c not in objects:
    c.notify(text)
 
 def destroy(self):
  for o in self.contents:
   o.move(NOWHERE)
  return super(RoomObject, self).destroy()
 
 def title(self):
  """Return the zone name as well as the room name."""
  if isinstance(self.location, objects.ZoneObject):
   return '[%s; %s]' % (self.location.title(), self.name)
  else:
   return '[%s]' % self.name
