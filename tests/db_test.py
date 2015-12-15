import sys, logging, os

sys.path.insert(0, '.')

logger = logging.getLogger('DB Tests')

import db
from objects import *

fname = 'aadvark.json'

def test_dump():
 o = BaseObject('Base')
 m = MobObject('Mob')
 p = PlayerObject('Player')
 r = RoomObject('Room')
 db.dump(fname)
 l = len(db.objects)
 logger.info('Current objects: %s.', db.objects)
 db.clear()
 assert not len(db.objects)
 db.load(fname)
 assert len(db.objects) >= l, '%s (%s -> %s).' % (db.objects, len(db.objects), l)

 os.remove(fname)
 logger.info('Removed DB file: %s.', fname)
