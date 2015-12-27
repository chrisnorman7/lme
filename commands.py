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

import server, re, objects, objects.players as players, logging, options, db, util, traceback, socket, platform, multiprocessing, psutil, os
from twisted.internet import reactor
from inspect import getdoc
from datetime import timedelta
from time import ctime
from memory import memory

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
 """Perform command for obj."""
 if not command:
  command = '\n'
 if hasattr(command, 'decode'):
  command = command.decode(options.args.default_encoding, errors = 'ignore')
 if options.args.log_commands:
  logger.info('%s entered command: %s', obj.title(), command)
 obj.commands.append(command)
 while len(obj.commands) > db.server_config['command_history_length']:
  del obj.commands[0]
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
  try:
   cmd = command.split()[0] + ' '
  except IndexError:
   cmd = '' # It's just a blank line... probably.
  for f in commands.values():
   if obj.access >= f.access and cmd in f.name:
    obj.notify('Command %s not understood. Did you mean %s?' % (cmd, f.name.split()[0]))
    break
  else:
   obj.notify('Command %s not found. If you are having trouble finding commands and their syntax, try typing @commands.' % cmd)

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
add_command('^@?quit$', do_quit)

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
do_commands.name = '@commands'
add_command('^@commands$', do_commands)

def do_say(obj, text):
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
add_command('''^(?:say |"|')([^$]*)$''', do_say)

def do_break(obj):
 """
 Causes a traceback for debugging purposes.
 
 Synopsis:
  break
 """
 raise RuntimeError('Yes, that broke alright.')
do_break.name = '@break'
do_break.access = players.PROGRAMMER
add_command('^@break$', do_break)

def do_eval(obj, text):
 """
 Evaluates some Python code.
 
 Synopsis:
  eval <code>
  ;<code>
 """
 logger.warning('%s (%s) evaluating code: %s', obj.title(), obj.transport.hostname, text)
 try:
  obj.notify(repr(eval(text)))
 except Exception as e:
  obj.notify(traceback.format_exc().replace('\n', '\r\n'))
 finally:
  return True
do_eval.name = 'eval ;'
do_eval.access = players.PROGRAMMER
add_command(r'^(?:eval|;)([^$]*)$', do_eval)

def do_uptime(obj):
 """
 Shows how long the server has been running for.
 
 Synopsis:
  uptime
  @uptime
 """
 return obj.notify('The server has been up since %s (%s).' % (ctime(server.started), timedelta(seconds = server.uptime())))
do_uptime.name = '@uptime'
add_command('^@uptime$', do_uptime)

def do_redo(obj, text):
 """
 Re-enter the last command.
 
 Synopsis:
  .
  .<text to append>
 
 Any text which appears after the . will be appended to the previous command and the command will be treated as a whole.
 """
 if len(obj.commands) > 1:
  cmd = obj.commands[-2]
  cmd += text
  do_command(obj, cmd)
 else:
  obj.notify('You have no commands to repeat.')
 return True
do_redo.name = '.'
add_command(r'^\.([^$]*)$', do_redo)

def do_shout(obj, text):
 """
 Shout text to everyone in the game.
 
 Synopsis:
  shout <text>
  !<text>
 
 <text> will be announced to everyone currently connected.
 """
 if text:
  db.notify_players('%s shouts, "%s"' % (obj.title(), text))
 else:
  obj.notify('Shout what?')
 return True
do_shout.name = 'shout !'
add_command('^(?:!|shout )([^$]*)$', do_shout)

def do_shutdown(obj, when, reason):
 """
 Shutdown the server after a certain period of time.
 
 Synopsis:
  shutdown <time>
  @shutdown <time>
 
 The server will need to be restarted from the console.
 """
 logger.info('Shutdown initialised by %s.', obj.title())
 def f2():
  """Actually perform the shutdown."""
  db.notify_players('The server will be shutting down in 5 seconds.')
  do_shutdown.delay = reactor.callLater(5, reactor.stop)
 def f1(when, reason):
  db.notify_players('The server will be shutting down for %s in %s second%s.' % (reason, when, '' if when== 1 else 's'))
  if when > 5:
   do_shutdown.delay = reactor.callLater(when - 5, f2)
  else:
   do_shutdown.delay = reactor.callLater(when, reactor.stop)
 obj.read(lambda text, player = obj, w = when, r = reason: f1(int(w), r.strip() or 'maintenance') if util.yes_or_no(text) else player.notify('Shutdown aborted.'), 'Are you sure you want to shutdown the server in %s second%s?' % (when, '' if when == '1' else 's'))
 return True
do_shutdown.name = '@shutdown'
do_shutdown.access = players.WIZARD
add_command('^@shutdown (\d+)([^$]*)$', do_shutdown)

def do_abort_shutdown(obj):
 """
 Abort a running shutdown.
 
 Synopsis:
  abort-shutdown
  @abort-shutdown
 """
 if hasattr(do_shutdown, 'delay'):
  do_shutdown.delay.cancel()
  db.notify_players('Shutdown aborted.')
  del do_shutdown.delay
 else:
  obj.notify('There is no shutdown in progress.')
 return True
do_abort_shutdown.name = '@abort-shutdown'
do_abort_shutdown.access = players.WIZARD
add_command('^@abort-shutdown$', do_abort_shutdown)

def do_ban(obj, command, host):
 """
 Ban or unban an IP address.
 
 Synopsis:
  @ban <hostname or IP address>
  @unban <hostname or IP address>
 
 When banned, nobody logging in from the provided hostname will be able to connect to the server.
 """
 try:
  ip = socket.gethostbyname(host)
  hostname = '%s (%s)' % (host, ip)
 except socket.error as e:
  obj.notify('Could not find any address for host %s: %s.' % (host, e))
 else:
  if command == 'ban':
   if ip in server.get_config('banned_hosts'):
    obj.notify('Host %s is already a banned host.' % hostname)
   else:
    server.get_config('banned_hosts').append(ip)
    obj.notify('Host %s added to banned hosts list.' % hostname)
  else:
   try:
    server.get_config('banned_hosts').remove(ip)
    obj.notify('Removed host %s from banned hosts list.' % hostname)
   except KeyError:
    obj.notify('Host %s is not a banned host.' % hostname)
 finally:
  return True
do_ban.name = '@ban @unban'
do_ban.access = players.WIZARD
add_command(r'^@(ban|unban) ([^$]+)$', do_ban)

def do_banned(obj):
 """
 List banned hosts.
 
 Synopsis:
  @banned
 Hosts ban be banned or unbanned with the @ban and @unban commands.
 """
 banned = server.get_config('banned_hosts')
 if banned:
  obj.notify('Banned hosts: %s.' % len(banned))
  for b in banned:
   obj.notify('%s (%s)' % (b, socket.gethostbyaddr(b)[0]))
  obj.notify('Done.')
 else:
  obj.notify('There are no banned hosts.')
 return True
do_banned.name = '@banned'
do_banned.access = players.PROGRAMMER
add_command('^@banned$', do_banned)

def do_info(obj):
 """
 Shows information about the running server.
 
 Synopsis:
  @info
 """
 mem = psutil.virtual_memory()
 proc_size = memory()
 obj.notify('Server information:')
 obj.notify('Python Version: %s.' % platform.python_version())
 obj.notify('PID: %s.' % os.getpid())
 obj.notify('Process Size: %.2fMB (%.2f bytes).' % (proc_size / (1024.0 ** 2), proc_size))
 obj.notify('Opperating System: %s.' % platform.platform())
 obj.notify('Processor: %s.' % (platform.processor() or 'Unknown'))
 obj.notify('Memory: Used %.2fMB of %.2fGB (%.2f%%).' % (mem.used / (1024.0 ** 2), mem.total / (1024.0 ** 3), mem.percent))
 obj.notify('Max Concurrent Threads: %s.' % multiprocessing.cpu_count())
 obj.notify('Objects in database: %s.' % len(db.objects))
 return True
do_info.name = '@info'
add_command('^@info$', do_info)
