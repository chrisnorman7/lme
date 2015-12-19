import sys, pytest

sys.path.insert(0, '.')

import server

def test_server_name():
 assert server.server_name()

def test_uptime():
 assert type(server.uptime()) == float

def test_set_config():
 server.set_config('test', 'Testing.')

def test_get_config():
 assert server.get_config('test') == 'Testing.'
 assert server.get_config('non-existant', False) == False

def test_clear_config():
 server.clear_config('test')
 with pytest.raises(KeyError):
  server.get_config('test')
