import sys

sys.path.insert(0, '.')

import passwords

def test_to_password():
 assert passwords.to_password('test')

def test_check_password():
 pwd = 'test'
 assert passwords.check_password(pwd, passwords.to_password(pwd))

def test_random_password():
 l = 19
 assert len(passwords.random_password(length = l)) == l
