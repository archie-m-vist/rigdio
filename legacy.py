from condition import *
from config import settings

class ConditionList:
   def __init__(self, pname = "NOPLAYER", tname = "NOTEAM", data = [], songname = "New Song", home = True, runInstructions = True):
      self.pname = pname
      self.tname = tname
      self.home = home
      self.songname = songname
      self.conditions = []
      self.instructions = []
      self.disabled = False
      self.startTime = 0
      self.event = None
      self.endType = "loop"
      self.pauseType = "continue"
      for tokenStr in data:
         tokens = processTokens(tokenStr)
         condition = buildCondition(tokens, pname=self.pname, tname=self.tname, home=self.home)
         if condition.isInstruction():
            self.instructions.append(condition)
         else:
            self.conditions.append(condition)
      if pname == "chant":
         self.instructions.append(EndInstruction(pname=self.pname, tname=self.tname, tokens=("stop",)))
      self.all = self.conditions + self.instructions
      if runInstructions:
         self.instruct()

   def __str__(self):
      output = "{}".format(basename(self.songname))
      for condition in self.conditions:
         output = output + ";" + str(condition)
      for instruction in self.instructions:
         output = output + ";" + str(instruction)
      return output

   def __repr__ (self):
      pname = self.pname
      tname = self.tname
      data = str(self).split(";")[1:]
      songname = self.songname
      home = self.home
      output = "ConditionList(pname={},tname={},data={},songname={},home={})"
      return output.format(pname,tname,data,songname,home)

   def __len__ (self):
      return len(self.all)

   def __iter__ (self):
      return self.all.__iter__()

   def __getitem__ (self, key):
      return self.all[key]

   def __setitem__ (self, key, value):
      temp = self.all[key]
      if temp.isInstruction():
         index = self.instructions.index(temp)
         self.instructions[index] = value
      else:
         index = self.conditions.index(temp)
         self.conditions[index] = value
      # insert new value where it was
      self.all[key] = value

   def instruct (self):
      for instruction in self.instructions:
         if instruction.allowUnloaded():
            print("Preparing {} instruction".format(instruction))
            instruction.prep(self)

   def append (self, item):
      self.all.append(item)
      if item.isInstruction():
         self.instructions.append(item)
      else:
         self.conditions.append(item)

   def disable (self):
      self.disabled = True

   def pop (self, index = 0):
      item = self.all.pop(index)
      if item.isInstruction():
         self.instructions.remove(item)
      else:
         self.conditions.remove(item)
      return item

   def check (self, gamestate):
      if self.disabled:
         raise UnloadSong
      for condition in self.conditions:
         print("Checking {}".format(condition))
         if not condition.check(gamestate):
            return False
      return True

   def toYML (self):
      # with no conditions, simply return song name
      if len(self.all) == 0:
         return basename(self.songname)
      # otherwise, store filename in dict
      output = {}
      output["filename"] = basename(self.songname)
      output["conditions"] = []
      for item in self.conditions:
         output["conditions"].append(item.toYML())
      output["instructions"] = []
      for item in self.instructions:
         output["instructions"].append(item.toYML())
      return output

def loadsong(filename):
   print("Attempting to load "+filename)
   filename = abspath(filename)
   if not ( isfile(filename) ):  
      raise Exception(filename+" not found.")
   source = vlc.MediaPlayer("file:///"+filename)
   return source

class ConditionPlayer (ConditionList):
   def __init__ (self, pname, tname, data, songname, home, song, type = "goalhorn"):
      ConditionList.__init__(self,pname,tname,data,songname,home,False)
      self.song = song
      self.type = type
      self.isGoalhorn = type=="goalhorn"
      self.fade = None
      self.endChecker = None
      self.startTime = 0
      self.firstPlay = True
      self.pauseType = "continue"
      self.instructionsStart = []
      self.instructionsPause = []
      self.instructionsEnd = []
      self.maxVolume = 100
      # repetition settings; may be changed by instructions
      norepeat = set(["victory"])
      self.repeat = (pname not in norepeat)
      self.instruct()
      self.song.set_rate(float(settings.speed))
      # hard override for events to stop them repeating
      if self.repeat and self.event is None:
         self.song.get_media().add_options("input-repeat=-1")
   
   def instruct (self):
      for instruction in self.instructions:
         print("Preparing {} instruction".format(instruction))
         instruction.prep(self)

   def reloadSong (self):
      self.song = loadsong(self.songname)
      print("reloading {}".format(self.songname))
      self.instruct()

   def play (self):
      if self.fade is not None:
         print("Song played quickly after pause, cancelling fade.")
         thread = self.fade
         self.fade = None
         thread.join()
      self.song.play()
      self.song.audio_set_volume(self.maxVolume)
      if self.firstPlay:
         for instruction in self.instructionsStart:
            instruction.run(self)
         self.firstPlay = False

   def adjustVolume (self, value):
      self.maxVolume = int(value)
      self.song.audio_set_volume(self.maxVolume)

   def pause (self, fade=None):
      if fade is None:
         fade = self.type in settings.fade and settings.fade[self.type]
      if fade:
         print("Fading out {}.".format(self.songname))
         self.fade = threading.Thread(target=self.fadeOut)
         self.fade.start()
      else:
         print("Pausing {}.".format(self.songname))
         for instruction in self.instructionsPause:
            instruction.run(self)
         self.song.pause()
   
   def onEnd (self, callback):
      events = self.song.event_manager()
      events.event_attach(vlc.EventType.MediaPlayerEndReached, callback)

   def fadeOut (self):
      i = 100
      while i > 0:
         if self.fade == None:
            break
         volume = int(self.maxVolume * i/100)
         self.song.audio_set_volume(volume)
         sleep(settings.fade["time"]/100)
         i -= 1
      for instruction in self.instructionsPause:
         instruction.run(self)
      self.song.pause()
      if self.song.get_media().get_state() == vlc.State.Ended:
         self.reloadSong()
      self.song.audio_set_volume(self.maxVolume)
      self.fade = None

   def disable (self):
      self.song.stop()
      super().disable()

class PlayerManager:
   def __init__ (self, clists, home, game):
      # song information
      self.clists = clists
      self.home = home
      self.game = game
      # derived information
      self.song = None
      self.lastSong = None
      self.pname = clists[0].pname
      self.futureVolume = None

   def __iter__ (self):
      for x in self.clists:
         yield x

   def adjustVolume (self, value):
      if self.song is not None:
         self.song.adjustVolume(value)
      self.futureVolume = value

   def getSong (self):
      # iterate over songs with while loop
      i = 0
      while i < len(self.clists):
         # try to check the condition list
         try:
            checked = self.clists[i].check(self.game)
         # if a song will no longer be played, check will raise UnloadSong
         except UnloadSong:
            # disable the ConditionListPlayer, closing the song file
            self.clists[i].disable()
            # deleted 
            del self.clists[i]
            # do not increment i, self.clists[i] is now the next song; continue
            continue
         # if conditions were met
         if checked:
            return self.clists[i]
         # if the song didn't succeed, move to the next
         i += 1
      # if no song was found, return nothing
      return None

   def playSong (self):
      # don't play multiple songs at once
      self.pauseSong()
      # get the song to play
      self.song = self.getSong()
      # if volume was stored, update it
      if self.futureVolume is not None:
         self.song.adjustVolume(self.futureVolume)
      # check if no song was found
      if self.song is None:
         raise SongNotFound(self.pname)
      # log song
      print("Playing",self.song.songname)
      # play the song
      self.song.play()
      # remove any data specific to this goal
      self.game.clearButtonFlags()

   def pauseSong (self):
      if self.song is not None:
         # log pause
         print("Pausing",self.song.songname)
         # pause the song
         self.song.pause()
         # clear self.song
         self.lastSong = self.song
         self.song = None

   def resetLastPlayed (self):
      if self.lastSong is not None:
         self.lastSong.reloadSong()
