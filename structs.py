"""Various pieces of information for use with objects."""

import os.path

# Body parts: used for wearing and displaying equipment.

body_parts = [
 'on head',
 'in left ear',
 'in right ear',
 'around neck',
 'about neck',
 'about shoulders',
 'on left shoulder',
 'on right shoulder',
 'across chest',
 'on chest',
 'about body',
 'around waist',
 'on legs',
 'on left knee',
 'on right knee',
 'on left ankle',
 'on right ankle',
 'on left foot',
 'on right foot'
]

# Room Types: Used for measuring how much end to take when moving.

room_types = {
 'water': 8, # Special value.
 'stone': 1,
 'grass': 2,
 'wood': 1,
 'metal': 1,
 'shallow water': 3,
 'sand': 4,
 'mud': 5,
 'marsh': 6
}

# Colours: Used in output.

_colours = {
 'reset': 0,
 'bold_on': 1,
 'italics_on': 3,
 'underline_on': 4,
 'inverse_on': 7,
 'strikethrough_on': 9,
 'bold_off': 22,
 'italics_off': 23,
 'underline_off': 23,
 'inverse_off': 27,
 'strikethrough_off': 29,
 'fg_black': 30,
 'fg_red': 31,
 'fg_green': 32,
 'fg_yellow': 33,
 'fg_blue': 34,
 'fg_magenta': 35,
 'fg_cyan': 36,
 'fg_white': 37,
 'fg_default': 39,
 'bg_black': 40,
 'bg_red': 41,
 'bg_green': 42,
 'bg_yellow': 43,
 'bg_blue': 44,
 'bg_magenta': 45,
 'bg_cyan': 46,
 'bg_white': 47,
 'bg_default': 49
}

colours = {} # The actual colours.

for x, y in _colours.items():
 colours[x] = '%s[%sm' % (chr(27), y)

with open(os.path.join(os.path.dirname(__file__), 'curses.txt'), 'r') as f:
 curse_words = f.read().split()
