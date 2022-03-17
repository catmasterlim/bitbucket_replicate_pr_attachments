import logging

log = logging.getLogger("helper")

# Necessary for debug/info messages to be processed by their respective handlers
log.setLevel(logging.DEBUG) 

# Outputs logs at debug level to log file
file_handler = logging.FileHandler('bitbucket-api.log')
file_handler_format = logging.Formatter('%(asctime)s | %(levelname)s | %(message)s')
file_handler.setFormatter(file_handler_format)
file_handler.setLevel(logging.DEBUG)

stream_handler = logging.StreamHandler()
stream_handler_format = logging.Formatter('%(asctime)s | %(levelname)s | %(message)s')
stream_handler.setFormatter(stream_handler_format)
stream_handler.setLevel(logging.INFO)

log.addHandler(file_handler)
log.addHandler(stream_handler)

log.debug('Starting runtime...')
