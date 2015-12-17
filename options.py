"""Command line arguments."""

import sys, logging
from argparse import ArgumentParser, FileType

parser = ArgumentParser()

parser.add_argument('-f', '--logfile', type = FileType('w'), default = sys.stdout, help = 'The log file')
parser.add_argument('-F', '--logformat', default = '[%(asctime)s] %(name)s.%(levelname)s: %(message)s', help = 'The log format')
parser.add_argument('-l', '--loglevel', choices = ['debug', 'info', 'warning', 'error', 'critical'], default = 'info', help = 'The logging level')
parser.add_argument('-e', '--defaultencoding', dest = 'default_encoding', default = 'utf-8', help = 'The default encoding to use')
parser.add_argument('-p', '--port', type = int, default = 4444, help = 'The server port')
parser.add_argument('-d', '--dumpfile', dest = 'dump_file', default = 'DB.json', help = 'Where to dump the database')
parser.add_argument('-c', '--log-commands', action = 'store_true', help = 'Log commands')

args = parser.parse_args([] if 'py.test' in sys.argv[0] else sys.argv[1:])

logging.basicConfig(stream = args.logfile, level = args.loglevel.upper(), format = args.logformat)
