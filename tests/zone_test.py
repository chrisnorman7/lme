import sys

sys.path.insert(0, '.')

import server, db
from objects import ZoneObject

z = ZoneObject('Test Zone')

def test_dump():
 assert z.dump()
def test_load():
 z.load(z.dump()[1])
