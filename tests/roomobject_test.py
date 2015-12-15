import sys, logging

sys.path.insert(0, '.')

import objects

logger = logging.getLogger('Room Tests')

r = objects.RoomObject('Test Room')
class TempObject(objects.BaseObject):
 def notify(self, text):
  super(TempObject, self).notify(text)
  logger.info('Notify: %s.', text)

objects.TempObject = TempObject

temp_object = TempObject('Temporary Test Object')

def test_extras():
 extra = r.add_extra('Test Extra', 'This is a test extra.')
 assert r.extras
 r.remove_extra(extra)

def test_is_light():
 assert r.is_light()

def test_is_safe():
 return r.is_safe()

def test_temp_object():
 assert temp_object

def test_temp_object_announce():
 temp_object.notify('Private notify')

def test_announce():
 r.announce('Announce.', temp_object)

def test_announce_all():
 r.announce_all('Announce all.')

def test_is_light_with_darkness():
 r.light = False
 assert r.description == r.dark_msg

def test_destroy():
 r.destroy()

def test_dump():
 assert r.dump()

def test_load():
 r.load(r.dump()[1])
