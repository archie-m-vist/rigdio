# taken from http://stackoverflow.com/a/616672 with some modifications
import sys

class Logger(object):
   def __init__(self, filename):
      self.terminal = sys.stdout
      self.log = open(filename, "w")

   def __del__(self):
      sys.stdout = self.terminal
      self.log.close()

   def write(self, message):
      self.terminal.write(message)
      self.log.write(message)  

   def flush(self):
      self.terminal.flush()
      self.log.flush()

def startLog (filename):
   sys.stdout = Logger(filename)
   sys.stderr = sys.stdout