import logging


class NukeboxLogger:

    '''
    '''

    def __init__(self, client):

        '''
        Logger constructor method
        '''

        # Set Up the Instance Variables
        # Store a Reference to the Caller
        self.client = client

        # Set the Logger Details and Level
        self.logger = logging.getLogger(self.client)
        self.logger.setLevel(logging.DEBUG)

        # If the Caller is the "Server"
        if 'Server' in self.client:
            fh = logging.FileHandler('jukebox_server.log')

        # If the Caller is the "Client"
        else:
            fh = logging.FileHandler('jukebox_client.log')

        # Set the Level of the File Handler
        fh.setLevel(logging.DEBUG)

        # Set up our Formatting
        formatter = logging.Formatter(
                                      ('%(asctime)s - '
                                       '%(name)s - '
                                       '%(levelname)s - '
                                       '%(message)s')
                                      )
        fh.setFormatter(formatter)

        # Add the File Handler to the Logger
        self.logger.addHandler(fh)

    def logInfo(self, msg):

        '''
        Logger for Info Messages
        '''

        self.logger.info(msg)
        print 'Info Message logged'
        return True

    def logDebug(self, msg):
        '''
        Logger for Debug Messages
        '''

        self.logger.debug(msg)
        print 'Debug Message logged'
        return True

    def logError(self, msg):
        '''
        Logger for Error Messages
        '''

        self.logger.error(msg)
        print 'Error Message logged'
        return True

    def logWarn(self, msg):
        '''
        Logger for Warning Messages
        '''

        self.logger.warning(msg)
        print 'Warning Message logged'
        return True

    def logCrit(self, msg):
        '''
        Logger for Critical Messages
        '''

        self.logger.critical(msg)
        print 'Critical Message logged'
        return True

    def log(self, msg, level):
        '''
        Logger Level Method
        - Tests the input string for a specified log level
        '''

        # Comparison Dictionary for Callbacks
        level_dict = {
            'info': self.logInfo,
            'debug': self.logDebug,
            'error': self.logError,
            'critical': self.logCrit,
            'warning': self.logWarn,
            }

        # Compares the Input String (the key) and Calls the Corresponding
        # Callback
        logged = level_dict[level](msg)

        # If the logged call was a Success
        if logged is True:
            return 'Logged!'

        # Otherwise Return False
        return False

#  ########################### Usage ##################################

# Store the logger.py file in the same directory as the script you want
# to log from (Twisted Client/Server) and import the file using:

# from logger.py import NukeboxLogger

# Next, create a logger Object and pass it the relevant details i.e. is
# this the Client or the Sever?

# Example, for the Server , this is what the call looks like:

# logger = NukeboxLogger('Server')


# That call just created a Nukebox logger object that uses the details
# inside the brackets (NukeboxLogger('Server') to customise the instance.

# Next, call the logger object's log method with 2 parameters:
# Parameter 1 is the message you want to log,
# Parameter 2 is the log level e.g. 'info' for general logging info or
# 'debug' for debug level messages


# Example, to log a error & a critical level message:

# logger.log('Someone pushed the big red button', 'warning')
# logger.log("We're all gonna di.........", 'critical')


# The log levels available to you are :
# info  (for general system stuff)
# debug (for more in depth stuff)
# error (speaks for itself really)
# warning (stuff you might need to display)
# critical (crash level stuff)
