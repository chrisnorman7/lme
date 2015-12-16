import sys

sys.path.insert(0, '.')

import server

def test_server_name():
 assert server.server_name()

def test_uptime():
 assert type(server.uptime()) == float
