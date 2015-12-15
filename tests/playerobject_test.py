import sys, logging

sys.path.insert(0, '.')

logger = logging.getLogger('Players Tests')

from objects.players import PlayerObject
import options, passwords

p = PlayerObject('Test Player')

uid = 'test'
pwd = 'test123'

def test_authenticate():
 p.uid = uid
 p.pwd = pwd
 logger.info('UID = %s, PWD = %s.', p.uid, p.pwd)
 assert uid.encode(options.args.default_encoding) == p.uid.encode(options.args.default_encoding)
 assert passwords.check_password(pwd, p.pwd)
 assert p.authenticate(uid, pwd)
 assert p.pwd != pwd

def test_dump():
 assert p.dump()

def test_load():
 p.load(p.dump()[1])
