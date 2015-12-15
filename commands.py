"""
Commands.

This is where the bulk of the server's player-side magic happens.

Create your commands then add them with add_command.

Commands should expect the following arguments:
obj - The object which called the command.
*args - The groups from the regexp match.
**kwargs - The groupdict from the regexp match.

If the command does not evaluate to True then the search algorithm will keep looking for commands.

Remember that do_command is called from a thread other than the main thread, so reactor.callFromThread must be used for anything which directly involves the network layer with the exception of obj.notify (which uses reactor.callFromThread anyway).

The following special properties can be added to commands to customise them:
name - a space-separated list of commands which can be used to invoke this command.
access - The level of access necessary to view and execute this command.
"""

import server, re, objects, objects.players as players, logging, options, db, util, traceback
from twisted.internet import reactor
from inspect import getdoc

commands = {} # Command regexp and functions.

logger = logging.getLogger('Commands')

def add_command(expr, func):
 """
 Add a function to the commands list.
 
 The entered command must match to expr.
 When found, func will be called with a player object, as well as args and kwargs as returned by match.groups(), and match.groupdict().
 """
 if not hasattr(func, 'name'):
  raise ValueError('%s has no name property.' % func)
 if not hasattr(func, 'access'):
  func.access = 0
 for x in dir(objects.players):
  if x.isupper() and func.access == getattr(objects.players, x):
   break # Found the access level.
 else:
  raise ValueError('%s is not a valid access level from objects.players.' % func.access)
 commands[re.compile(expr)] = func

def do_command(obj, command):
 command = command.decode(options.args.default_encoding, errors = 'ignore')
 if options.args.log_commands:
  logger.info('%s entered command: %s', obj.title(), command)
 for cmd, func in commands.items():
  if obj.access >= func.access:
   m = cmd.match(command)
   if m:
    try:
     if func(obj, *m.groups(), **m.groupdict()):
      break
    except Exception as e:
     cmd = func.name.split()[0]
     obj.notify('While executing command %s, an error was raised. See log for details.' % cmd)
     logger.critical('While executing command %s for player %s (%s), the following exception was raised:', cmd, obj.title(), obj.transport.hostname)
     logger.exception(e)
 else:
  cmd = command.split()[0]
  for f in commands.values():
   if obj.access >= f.access and cmd in f.name:
    obj.notify('Command not understood. Did you mean %s?' % f.name.split()[0])
    break
  else:
   obj.notify('Command %s not found. If you are having trouble finding commands and their syntax, try typing commands.' % cmd)

def do_quit(obj):
 """
 Disconnect from the server.
 
 Synopsis:
  quit
  @quit
 """
 obj.notify(db.server_config['disconnect_msg'])
 obj.transport.loseConnection()
 return True
do_quit.name = 'quit @quit'
add_command('^[@]?quit$', do_quit)

def do_commands(obj, *args, **kwargs):
 """
 Lists all commands.
 
 Synopsis:
  commands
  @commands
 """
 obj.notify('Commands listing:')
 i = 0
 for f in commands.values():
  if obj.access >= f.access:
   i += 1
   obj.notify('%s: %s' % (util.english_list(f.name.split(), and_string = 'or').capitalize(), getdoc(f).strip().split('\n')[0]))
 obj.notify('Commands: %s.' % i)
 return True
do_commands.name = 'commands @commands'
add_command('^[@]?commands$', do_commands)

def do_say(obj, command, text):
 """
 Speak some text.
 
 Synopsis:
  say <text>
  "<text>
  '<text>
 
 Speaks <text> to everyone in the same room.
 """
 if obj.location != objects.NOWHERE:
  if text:
   obj.notify('You say, "%s"' % text)
   obj.location.announce('%s says, "%s"' % (obj.title(), text), obj)
  else:
   obj.notify('You say nothing, good job.')
   obj.location.announce('%s opens %s mouth and shuts it again.' % (obj.title(), obj.gender.his), obj)
 else:
  obj.notify('You cannot speak here.')
 return True
do_say.name = 'say " \''
add_command('''^(say|"|')[ ]?([^$]*)$''', do_say)

def do_fuckup(obj):
 """
 Causes a traceback for debugging purposes.
 
 Synopsis:
  fuck
  fuckup
 """
 raise RuntimeError('Yes, that was a fuck up alright.')
do_fuckup.name = 'fuck fuckup'
do_fuckup.access = players.PROGRAMMER
add_command('^fuck(?:up)?$', do_fuckup)

def do_eval(obj, text):
 """
 Evaluates some Python code.
 
 Synopsis:
  eval <code>
  ;<code>
 """
 logging.warning('%s (%s) evaluating code: %s', obj.title(), obj.transport.hostname, text)
 try:
  obj.notify(eval(text))
 except Exception as e:
  obj.notify(traceback.format_exc().replace('\n', '\r\n'))
 finally:
  return True
do_eval.name = 'eval ;'
do_eval.access = players.PROGRAMMER
add_command(r'^(?:eval|\;)([^$]*)$', do_eval)
