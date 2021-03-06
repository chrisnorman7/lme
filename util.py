"""Utility functions."""

import string, structs, db, re

numerical_match = re.compile(r'^(\d+.|)([^$]+)$')

def disallowed_name(name):
 """Checks a name conforms to the supported format."""
 if contains_curses(name):
  return 'Names must not contain any profanity.'
 elif name.count(' ') > 1:
  return 'Only one space character allowed in a name.'
 elif name.strip(string.ascii_letters + ' '):
  return 'Your name must contain only the letters a to z (upper or lower case), with the first and last names separated by a space.'
 else:
  return None

def contains_curses(text):
 """Checks given text for curse words."""
 text = text.lower()
 curses = 0 # The number of curse words found.
 for curse in structs.curse_words:
  if curse in text:
   curses += 1
 return curses

def format_colour(text):
 """Formats text to contain colour."""
 return text.format(**structs.colours)

def english_list(value, sep = ', ', and_string = 'and'):
 """Make an english list out of value."""
 l = len(value)
 if not l:
  return ''
 elif l == 1:
  return str(value[0])
 else:
  return '%s%s%s %s' % (sep.join([str(v) for v in value[:-1]]), sep, and_string, value[-1])

def yes_or_no(text):
 return text in ['y', 'yes']

def match(text, objects, prop = 'name', method = 'startswith'):
 """
 Match text against a list of objects.
 
 Checks the prop property of each object to see if it's .method method returns something which evaluates to True.
 """
 text = text.lower()
 m = numerical_match.match(text)
 if m:
  index, search = m.groups()
  results = [o for o in objects if getattr(getattr(o, prop).lower(), method)(search)]
  if index:
   try:
    return [results[int(index[:-1])]]
   except IndexError:
    return []
  else:
   return results

def match_player(text, players = None):
 """Match a list of players. players defaults to db.get_players()."""
 return match(text, players if players else db.get_players(), method = '__contains__')
