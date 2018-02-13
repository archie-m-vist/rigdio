import sys
import json

import win32pipe, win32file, win32api

from threading import Thread, Lock
from .event import buildEvent

class SENPAINotFound (Exception):
   """Raised when the program is unable to find the pipe."""

   def __init__ (self):
      super().__init__("Unable to find SENPAI pipe. Is SENPAI server running?")

class SENPAIConnectionFailed (Exception):
   """Raised when the program is unable to connect for some other reason."""
   pass

class SENPAIPipeClosed (Exception):
   """Raised when the pipe is closed by the server."""
   
   def __init__ (self):
      super().__init__("Pipe closed by SENPAI server.")

class SENPAI:
   def __init__ (self):
      self.pipe = None

   def __enter__ (self):
      self.open()
      return self

   def __exit__ (self, type, value, traceback):
      self.close()

   def open (self):
      try:
         self.pipe = win32file.CreateFile(r"\\.\pipe\SEN_P-AI", win32file.GENERIC_READ | win32file.GENERIC_WRITE, 0, None, win32file.OPEN_EXISTING, 0, None)
      except win32api.error as e:
         # can't connect to pipe
         if e.winerror == 2:
            raise SENPAINotFound()
         # handle as regular exception
         else:
            raise SENPAIConnectionFailed("win32 error #{} occurred while connecting to SENPAI pipe:\n{}: {}".format(e.winerror,e.funcname,e.strerror))
      except Exception as e:
         raise SENPAIConnectionFailed("Exception occurred while connecting to SENPAI pipe: {}\n{}".format(type(e).__name__),e)

   def close (self):
      win32api.CloseHandle(self.pipe)

   def readEvent (self):
      # read size
      try:
         data = win32file.ReadFile(self.pipe, 4)
      except win32api.error as e:
         # in case of closed pipe, terminate gracefully
         if e.winerror == 109:
            raise SENPAIPipeClosed()
         # handle as regular exception
         else:
               raise SENPAIConnectionFailed("win32 error #{} occurred while reading next SENPAI message size:\n{}: {}".format(e.winerror,e.funcname,e.strerror))
      except Exception as e:
         raise SENPAIConnectionFailed("Exception occurred while reading next SENPAI message size: {}\n{}".format(type(e).__name__),e)
      # read size from data
      size = int.from_bytes(data[1],byteorder="little",signed=True)
      if size is 0:
         raise ValueError("SENPAI sent message of size 0.")
      try:
         data = win32file.ReadFile(self.pipe, size)
      except win32api.error as e:
         # in case of closed pipe, terminate gracefully
         if e.winerror == 109:
            raise SENPAIPipeClosed()
         # handle as regular exception
         else:
               raise SENPAIConnectionFailed("win32 error #{} occurred while reading next SENPAI message data:\n{}: {}".format(e.winerror,e.funcname,e.strerror))
      except Exception as e:
         raise SENPAIConnectionFailed("Exception occurred while reading next SENPAI message data: {}\n{}".format(type(e).__name__),e)
      raw = data[1].decode('utf-8')
      return buildEvent(json.loads(raw))

class ThreadSENPAI:
   """
      A SENPAI wrapper intended for multithreaded access.

      Any object which implements methods from SENPAIListener can be registered as a listener through addListener.
      The object will wait in its own thread, 
   """
   def __init__ (self):
      self.senpai = SENPAI()
      self.listeners = []
      self.locks = {
         "listen": Lock()
      }
      self.thread = None

   def addListener (self, listener):
      with self.locks["listen"]:
         self.listeners.append(listener)

   def start (self):
      print("SENPAI client running in multithreaded mode.")
      self.senpai.open()
      self.thread = Thread(target=self.loop, daemon=True).start()

   def loop (self):
      while True:
         event = self.senpai.readEvent()
         with self.locks["listen"]:
            for listener in self.listeners:
               # spawn thread to handle things for the listener
               Thread(target=listener.handleEvent,args=(event,)).start()

