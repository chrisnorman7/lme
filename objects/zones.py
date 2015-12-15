"""Group rooms together."""

from objects import BaseObject

class ZoneObject(BaseObject):
 
 def __init__(self, *args, **kwargs):
  super(ZoneObject, self).__init__(*args, **kwargs)
  self.dump_properties += [
   'reset_interval'
  ]
  self.last_reset = 0.0
  self.reset_interval = 20.0 # Reset interval in minutes.
