"""Mobs. Base class for player objects."""

from objects import BaseObject
import logging, db, genders

logger = logging.getLogger('Mobile Objects')

class MobObject(BaseObject):
 @property
 def hp(self):
  return self.max_hp if self._hp == None else self._hp
 
 @hp.setter
 def hp(self, value):
  self._hp = value
 
 @property
 def aur(self):
  return self.max_aur if self._aur == None else self._aur
 
 @aur.setter
 def aur(self, value):
  self._aur = value
 
 @property
 def end(self):
  return self.max_end if self._end == None else self._end
 
 @end.setter
 def end(self, value):
  self._end = value
 
 def __init__(self, *args, **kwargs):
  super(MobObject, self).__init__(*args, **kwargs)
  self.dump_properties += [
   'blind',
   'speed',
   'level',
   'experience',
   'max_hp',
   '_hp',
   'con',
   'str',
   'dex',
   'mag',
   'bra',
   'max_aur',
   '_aur',
   'max_end',
   '_end',
   'res'
  ]
  self.dump_object_properties += [
   'wearing',
  ]
  self.affects = {} # The spells affecting this object.
  self.blind = False # If True, this object cannot see.
  self.speed = 2.0 # The time to wait between strikes.
  self.level = 0 # The level of this object.
  self.experience = 100 # How many experience points this object has.
  self.gender = genders.NEUTRAL
  self.wearing = {} # What this object is wearing.
  self.can_teach = {} # What this object can teach.
  self.skills = {} # The skills this object has learned.
  self.spells = {} # The spells this object has learned.
  # The below properties concern stats. See Stats.txt for details.
  self.max_hp = 5 # Max hp.
  self._hp = None # Current hp or None for max.
  self.con = 5 # Constitution.
  self.str = 2 # Strength.
  self.dex = 2 # Dexterity.
  self.mag = 2 # Magic.
  self.bra = 2 # Brain.
  self.max_aur = 5 # Max aur.
  self._aur = None # Current aur or None for full.
  self.max_end = 5 # Max end.
  self._end = None # Current end or None for full.
  self.res = 2 # resolve.
 
 def dump(self):
  stuff = super(MobObject, self).dump()
  stuff[1]['gender'] = genders.genders.index(self.gender)
  return stuff
 
 def load(self, stuff):
  super(MobObject, self).load(stuff)
  try:
   self.gender = genders.genders[stuff['gender']]
  except KeyError:
   logger.critical('No gender found for object %s.', self.title())
