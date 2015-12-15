import sys, logging

logger = logging.getLogger('Util Tests')

sys.path.insert(0, '.')

import util

def test_contains_curses():
 assert util.contains_curses('Fuck you asshole.')
 assert not util.contains_curses('Hello world.')

def test_disallowed_name():
 assert not util.disallowed_name('Chris Norman')
 assert util.disallowed_name('Fuck You')
 assert util.disallowed_name('Cunt.lick')
 assert not util.disallowed_name('Jessica')
 assert util.disallowed_name('chris.norman2@googlemail.com')
 assert util.disallowed_name('a.b.c')
 assert util.disallowed_name('fhm123')

def test_format_colour():
 logger.info(util.format_colour('{bold_on}This text should be {fg_blue}blue{fg_default}{bold_off}.{reset}'))

def test_english_list():
 assert util.english_list([]) == ''
 assert util.english_list(['hello']) == 'hello'
 assert util.english_list(['hello', 'world']) == 'hello, and world'
 assert util.english_list(['fruit', 'nut', 'cream']) == 'fruit, nut, and cream'
 assert util.english_list(['male', 'female'], and_string = 'or') == 'male, or female'
