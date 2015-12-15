import sys

sys.path.insert(0, '.')

from objects.mobs import MobObject

m = MobObject('Test Mob')

def test_hp():
 assert m.hp == m.max_hp

def test_end():
 assert m.end == m.max_end

def test_aur():
 assert m.aur == m.max_aur

def test_dump():
 assert m.dump()

def test_load():
 m.load(m.dump()[1])
