if __name__ == '__main__':
 import options, sys, server, logging, db, os.path
 logging.info('Starting %s.', server.server_name())
 logging.debug('Command logging is %sabled.', 'en' if options.args.log_commands else 'dis')
 from twisted.internet import reactor
 if not os.path.isfile(options.args.dump_file):
  logging.info('Creating empty database.')
  with open(options.args.dump_file, 'w') as f:
   f.write('{}')
 db.load()
 server.port = server.initialise()
 reactor.run()
