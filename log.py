# -*- coding: utf8 -*-

class Level(object):
    """Logging Levels"""

    DEBUG = 0
    TRANSFER = 1
    USER = 2

def put_stdout(prefix, message):
    """Print a log message to stdout"""
    print("{0} {1}".format(prefix, message))

class Logger(object):
    """A simple logging class"""

    def __init__(self, output, level):
        self.level = level
        self.out = output

    def put(self, prefix, data, levels):
        """Write the log message to self.out"""
        if self.level in levels or len(levels) == 0:
            self.out(prefix, data)

    def info(self, data):
        """Inform the user about what's happening"""
        self.put("[INFO]", data, [Level.DEBUG, Level.TRANSFER, Level.USER])

    def warning(self, data):
        """Warn the user about behaviour that may be unexpected"""
        self.put("[WARNING]", data, [Level.DEBUG, Level.TRANSFER])

    def error(self, data):
        """Display an error message"""
        self.put("[ERROR]", data, [])

    def debug(self, data):
        """Display a debugging message"""
        self.put("[DEBUG]", data, [Level.DEBUG])

    def recv(self, data):
        """Inform about a message that was received"""
        self.put("<<", data, [Level.DEBUG, Level.TRANSFER])

    def send(self, data):
        """Inform about a message that was sent"""
        self.put(">>", data, [Level.DEBUG, Level.TRANSFER])

