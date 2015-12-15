import logging, sys, pytest

sys.path.insert(0, '.')

import server, objects, db

o = objects.BaseObject('Test Object')
target = objects.BaseObject('Test Target')
temporary = objects.BaseObject('Temporary Object.')

def test_exists():
 assert o in db.objects
 assert temporary in db.objects
 assert target in db.objects

def test_move_to_valid():
 """Move target to temporary."""
 target.move(temporary)
 o.move(target)
 assert target.location == temporary

def test_locations():
 logging.info('Locations for %s: %s.', o, o.locations())

def test_move_to_self():
 """Move o to o (should fail)."""
 with pytest.raises(objects.ContainmentError):
  o.move(o)

def test_move_to_container():
 # First make sure they're all OK to be moved.
 o.move(objects.NOWHERE)
 target.move(objects.NOWHERE)
 temporary.move(objects.NOWHERE)
 o.move(target)
 target.move(temporary)
 assert temporary in o.locations()
 with pytest.raises(objects.ContainmentError):
  o.move(temporary)

def test_move_to_nowhere():
 o.move(objects.NOWHERE)

def test_notify():
 assert o.notify('Testing.') == False

def test___str__():
 logging.info('o.__str__ = %s.', str(o))

def test_destroy():
 o.destroy()
 assert o not in db.objects

def test_description():
 assert o.description == objects.NOTHINGSPECIAL
 d = 'Test Description.'
 o.description = d
 assert o.description == d
 o.description = ''
 assert o.description == objects.NOTHINGSPECIAL

def test_name():
 assert o.title() == o.name

def test_format_message():
 logging.info('Format_message returned: %s.', o.format_message('{player_name}, {player_title}, {name}, {title}, {location_name}, {location_title}'))

def test_drop():
 logging.info('Drop: you = %s, other = %s.', o.format_message(o.drop_msg), o.format_message(o.odrop_msg))

def test_take():
 logging.info('Take: You = %s, other = %s.', o.format_message(o.take_msg), o.format_message(o.otake_msg))

def test_dump():
 logging.info('Dump = %s.', o.dump())

def test_load():
 o.load(o.dump()[1])
