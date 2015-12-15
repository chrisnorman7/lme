import sys, pytest

sys.path.insert(0, '.')

import commands

def test_add_command():
 f = lambda obj: None
 with pytest.raises(ValueError):
  commands.add_command('', f)
 f.name = 'test'
 commands.add_command('', f)
 assert not f.access
 f.access = 'tits'
 with pytest.raises(ValueError):
  commands.add_command('', f)
 f.access = commands.objects.players.WIZARD
 commands.add_command('', f)
 assert f.access == commands.objects.players.WIZARD
