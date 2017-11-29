import threading
from time import sleep
from os.path import basename, abspath, isfile
import vlc

# needed for prompts
from tkinter import *
from tkinter.simpledialog import Dialog
import tkinter.messagebox as messagebox

from config import settings
from rigdio_except import UnloadSong, PlayNextSong
from rigdio_util import timeToSeconds

binaryOperators = set(["<", ">", "<=", ">=", "==", "!="])
unloadableOperators = set(["<", "<=", "=="])

class Condition:
   null = "nullCond"

   def __init__(self, pname = "", tname = "", home = True, **kwargs):
      super().__init__(**kwargs) # initialise Object()
      self.pname = pname
      self.tname = tname
      self.home = home

   def check(self, gamestate):
      """
         Checks if a condition is true or not.
         
         Arguments:
          - gamestate (GameState): state of the game.
      """
      raise NotImplementedError("Condition subclass must override check().")

   def isInstruction (self):
      """
         Checks if something is a Condition or an Instruction. There is no need to override this.

         Return:
          - <code>True</code> if the object is an Instruction, <code>False</code> if the object is a Condition.
      """
      return False

   def type (self):
      """
         Name of this condition type.

         This is the string used to mark the condition in .4ccm files.
      """
      raise NotImplementedError("Condition subclass must override type().")

   def tokens (self):
      """
         Gives this Condition as a list of tokens, EXCLUDING the type of the condition.

         In essence, these are the tokens passed to the constructor, and listed after the condition name in files.
      """
      raise NotImplementedError("Condition subclass must override tokens().")

   def __str__ (self):
      return "{} {}".format(self.type()," ".join(self.tokens())).strip()

   def __repr__ (self):
      return "ConditionList.buildCondition(pname={},tname={},home={},tokens={})".format(self.pname,self.tname,self.home,str(self).split(" "))
      

class ArithCondition (Condition):
   desc = """Superclass for all conditions that evaluate an arithmetic expression."""

   def __init__(self, **kwargs):
      super().__init__(**kwargs)

   def check (self, gamestate):
      args = self.args(gamestate)
      return eval(self.expression().format(*args))

   def args (self, gamestate):
      raise NotImplementedError("ArithCondition subclass must override args().")

   def expression (self):
      raise NotImplementedError("ArithCondition subclass must override expression().")


class GoalCondition (ArithCondition):
   desc = """Plays when the number of goals this player has scored meet the condition."""

   def __init__(self, tokens, **kwargs):
      super().__init__(**kwargs)
      if tokens[0] == "=":
         tokens[0] = "=="
      if tokens[0] not in binaryOperators:
         raise ValueError("invalid GoalCondition operator "+tokens[0]+"; valid operators are "+list(binaryOperators))
      self.comparison = "{} "+tokens[0]+" "+tokens[1]
   
   def type (self):
      return "goals"

   def tokens (self):
      return self.comparison.split(" ")[1:]

   def expression (self):
      return self.comparison

   def args (self, gamestate):
      return (gamestate.player_goals(self.pname,self.home),)

class EveryCondition (ArithCondition):
   desc = """Plays when the number of goals is divisible by the given number."""

   def __init__(self, tokens, **kwargs):
      super().__init__(**kwargs)
      self.comparison = "{} % "+tokens[0]+" == 0"
      self.num = tokens[0]

   def type (self):
      return "every"

   def tokens (self):
      return [str(self.num)]

   def args (self, gamestate):
      return (gamestate.player_goals(self.pname,self.home),)

   def expression(self):
      return self.comparison

class ComebackCondition (Condition):
   desc = """Plays when the team was behind prior to this goal being scored. Equivalent to lead <= 0."""

   def __init__(self, tokens, **kwargs):
      super().__init__(**kwargs)

   def check(self,gamestate):
      return gamestate.team_score(self.home) <= gamestate.opponent_score(self.home) and gamestate.opponent_score(self.home) > 0

   def type (self):
      return "comeback"

   def tokens (self):
      return []

class OpponentCondition (Condition):
   desc = """Plays when the opponent is one of the listed teams (separated by spaces, exclude slashes from ends)."""

   def __init__(self, tokens, **kwargs):
      super().__init__(**kwargs)
      self.others = []
      for token in tokens:
         if " " in token:
            self.others.extend(token.split())
         else:
            self.others.append(token)


   def check(self,gamestate):
      return gamestate.opponent_name(self.home) in self.others

   def type (self):
      return "opponent"

   def tokens (self):
      return self.others

class FirstCondition (Condition):
   desc = """Plays if this is the first goal that the team has scored in this match."""
   
   def __init__ (self, tokens, **kwargs):
      super().__init__(**kwargs)

   def check(self, gamestate):
      return gamestate.team_score(self.home) == 1

   def type (self):
      return "first"

   def tokens (self):
      return []

class LeadCondition (GoalCondition):
   desc = """Plays if the goal difference (yourteam - theirteam) meets the given condition."""

   def __init__ (self, **kwargs):
      # pass tokens up to GoalCondition, the only difference in handling is in args()
      try:
         super().__init__(**kwargs)
      except ValueError:
         raise ValueError("invalid LeadCondition operator "+tokens[0]+"; valid operators are "+list(binaryOperators))

   def args(self, gamestate):
      gd = gamestate.team_score(self.home) - gamestate.opponent_score(self.home)
      return (gd,)

   def type (self):
      return "lead"

   # other methods don't need to be implemented because they're the same as GoalCondition

class MatchCondition (Condition):
   desc = """Plays if the match any of the listed types."""
   types = ["Group", "RO16", "Quarterfinal", "Semifinal", "Final", "Third-Place", "Boss", "Consolation"]
   knockout = ["RO16", "Quarterfinal", "Semifinal", "Final", "Third-Place"]

   def __init__ (self, tokens, **kwargs):
      super().__init__(**kwargs)
      if len(tokens) == 1 and tokens[0].lower() == "knockouts":
         tokens = MatchCondition.knockout
      self.lst = set([x.lower() for x in tokens])

   def check (self, gamestate):
      return gamestate.gametype.lower() in self.lst

   def type (self):
      return "match"

   def tokens (self):
      return list(self.lst)

class HomeCondition (Condition):
   desc = """Plays if the team is at home. (Use 'not home' for away.)"""

   def __init__(self, tokens, **kwargs):
      super().__init__(**kwargs)

   def check (self, gamestate):
      return self.home

   def type (self):
      return "home"

   def tokens (self):
      return []

class OnceCondition (Condition):
   desc = """Plays this song exactly once."""

   def __init__(self, tokens, **kwargs):
      super().__init__(**kwargs)
      self.okay = True

   def check (self, gamestate):
      if self.okay:
         self.okay = False
         return True
      raise UnloadSong

   def type (self):
      return "once"

   def tokens (self):
      return []

class MostGoalsCondition (Condition):
   desc = """Plays when either this player, or the specified player, has scored the most goals for this team in the match."""

   def __init__(self, tokens, pname=None, **kwargs):
      if len(tokens) > 0:
         super().__init__(pname=tokens[0],**kwargs)
         self.specified = tokens[0]
      else:
         super().__init__(pname=pname,**kwargs)
         self.specified = None

   def check (self, gamestate):
      scorers = gamestate.team_scorers(self.home)
      mygoals = gamestate.player_goals(self.pname,self.home)
      for player in scorers:
         if mygoals < scorers[player]:
            return False
      return True

   def tokens (self):
      if self.specified is None:
         return []
      else:
         return [self.specified]

   def type (self):
      return "mostgoals"

class PromptCondition (Condition):
   def __init__ (self, dtype, **kwargs):
      super().__init__(**kwargs)
      self.dtype = dtype

   def check (self, gamestate):
      if self.needsPrompt(gamestate):
         dialog = self.dtype(gamestate.instance)
         results = dialog.results
         return self.checkResults(gamestate,results)
      else:
         return self.checkStored(gamestate)

class TimeCondition (PromptCondition):
   class Prompt (Dialog):
      def __init__ (self, *args, **kwargs):
         super().__init__(*args, **kwargs)

      def body (self, frame):
         Label(frame,text="When was the goal scored (minute)?").pack()
         self.inputVar = StringVar()
         entry = Entry(frame,textvariable=self.inputVar)
         entry.pack()
         entry.focus()

      def validate (self):
         try:
            int(self.inputVar.get())
         except:
            messagebox.showwarning("Input Error", "Goal time must be an integer.")
            return False
         return True

      def apply (self):
         self.results = [int(self.inputVar.get())]

   def __init__ (self, tokens, **kwargs):
      super().__init__(dtype=TimeCondition.Prompt,**kwargs)
      if tokens[0] == "=":
         tokens[0] = "=="
      if tokens[0] not in binaryOperators:
         raise ValueError("invalid GoalCondition operator "+tokens[0]+"; valid operators are "+list(binaryOperators))
      self.operator = tokens[0]
      try:
         self.time = int(tokens[1])
      except:
         raise ValueError("Invalid TimeCondition token {}; must be integer.".format(tokens[1]))

   def needsPrompt (self, gamestate):
      return gamestate.time == None

   def checkResults (self, gamestate, results):
      # remove the song from the list if it's later in the game, to save ram from shit like /remi/
      gamestate.time = results[0]
      return self.checkStored(gamestate)

   def checkStored (self, gamestate):
      if gamestate.time > self.time and self.operator in unloadableOperators:
         raise UnloadSong
      return eval("{} {} {}".format(gamestate.time, self.operator, self.time))

   def type (self):
      return "time"

   def tokens (self):
      return [self.operator, str(self.time)]

class MetaCondition (Condition):
   def __init__ (self, tokens, **kwargs):
      super().__init__(**kwargs)
      self.sub = []
      temp = (" ".join(tokens)).split(",")
      for item in temp:
         self.sub.append(ConditionList.buildCondition(pname=self.pname,tname=self.tname,tokens=item.split(" "),home=self.home))

   def tokens (self):
      result = ",".join([str(x) for x in self.subconditions()])
      return result.split(" ")

   def subconditions (self):
      return self.sub

class NotCondition (MetaCondition):
   desc = """Plays when the given condition is false."""

   def __init__(self, tokens, condition = None, **kwargs):
      if condition is not None:
         kwargs["tokens"] = [condition.type, *condition.tokens()]
         home = condition.home
      super().__init__(tokens=tokens,**kwargs)

   def type (self):
      return "not"

   def check(self, gamestate):
      return not self.subconditions()[0].check(gamestate)

class Instruction:
   """
      Class used for something which modifies a ConditionPlayer rather than determining when it will play.

      This is a purely internal distinction; Instruction and Condition objects are manipulated and created the same ways by editing files or using rigDJ.
   """
   def isInstruction (self):
      return True

   def prep (self, player):
      """
         Prepares this instruction for later use (registering it to the start, end, or pause instruction list).
      """
      raise NotImplementedError("Instruction subclass must override prep().")

   def run (self, player):
      """
         Applies this instruction to a given media player object.
      """
      raise NotImplementedError("Instruction subclass must override run().")

   def __str__ (self):
      return "{} {}".format(self.type()," ".join(self.tokens()))

   def __repr__ (self):
      return "ConditionList.buildCondition(pname={},tname={},home={},tokens={})".format(self.pname,self.tname,self.home,str(self).split(" "))

   def type (self):
      raise NotImplementedError("Instruction subclass must override type().")

   def tokens (self):
      """
         Gives this Instruction as a list of tokens, EXCLUDING the type of the condition.

         In essence, these are the tokens passed to the constructor.
      """
      raise NotImplementedError("Instruction subclass must override tokens().")

class StartInstruction (Instruction):
   desc = """Starts the file at the given time (in min:sec format)."""

   def __init__ (self, tokens, **kwargs):
      timestring = tokens[0]
      self.rawTime = timestring
      self.startTime = int(1000*timeToSeconds(timestring))

   def prep (self, player):
      player.instructionsStart.append(self)
      player.startTime = self.startTime

   def run (self, player):
      player.song.set_time(self.startTime)

   def type (self):
      return "start"

   def tokens(self):
      return [self.rawTime]

class PauseInstruction (Instruction):
   desc = """Specify action taken when goalhorn is paused."""
   types = ["continue", "restart"]

   def __init__ (self, tokens, **kwargs):
      self.every = 1
      if tokens[0] not in PauseInstruction.types:
         raise ValueError("Unrecognised pause type (allowed values: {}).".format(", ".join(PauseInstruction.types)))
      if len(tokens) > 1:
         if tokens[1] == "every":
            self.every = int(tokens[2])
      self.command = tokens[0]

   def prep (self, player):
      player.instructionsPause.append(self)
      self.played = 0

   def run (self, player):
      self.played += 1
      if self.command == "continue":
         return
      if self.played % self.every == 0:
         if self.command == "restart":
            player.song.set_time(player.startTime)

   def type (self):
      return "pause"

   def tokens (self):
      return [self.command]

class EndInstruction (Instruction):
   desc = """Specify action taken when goalhorn reaches the end."""
   types = ["loop", "stop"]

   def __init__ (self, tokens, **kwargs):
      if tokens[0] not in EndInstruction.types:
         raise ValueError("Unrecognised end type (allowed values: {}).".format(", ".join(EndInstruction.types)))
      self.command = tokens[0]

   def prep (self, player):
      player.instructionsEnd.append(self)
      if self.command != "loop":
         player.song.get_media().add_options("input-repeat=0")

   def run (self, player):
      if self.command == "stop":
         player.reloadSong()
      elif self.command == "next":
         raise PlayNextSong

   def type (self):
      return "end"

   def tokens(self):
      return [self.command]

conditions = {
   "goals" : GoalCondition,
   "comeback" : ComebackCondition,
   "first" : FirstCondition,
   "opponent" : OpponentCondition,
   "lead" : LeadCondition,
   "match" : MatchCondition,
   "home" : HomeCondition,
   "once" : OnceCondition,
   "mostgoals" : MostGoalsCondition,
   # prompt
   "time" : TimeCondition,
   # meta
   "not" : NotCondition,
   "every" : EveryCondition,
   # instruction
   "start" : StartInstruction,
   "pause" : PauseInstruction,
   "end" : EndInstruction
}

def processTokens (tokenStr):
   data = tokenStr.split()
   i = 0
   while i < len(data):
      # escape character
      if data[i][0] == "\\":
         data[i] = data[i][1:]
      # quoted string semantics
      elif data[i][0] == "[":
         data[i] = list(data[i])
         while data[i+1][-1] != "]" or data[i+1][-2] == "\\":
            temp = list(data.pop(i+1))
            # remove escapes on end of string
            if temp[-1] == "]" and temp[-2] == "\\":
               temp.pop(-2)
            data[i].append(" ")
            data[i].extend(temp)
         data[i].append(" ")
         data[i].extend(list(data.pop(i+1)))
         data[i] = "".join(data[i][1:-1]) # remove the []
      i += 1
   return data

class ConditionList:
   def buildCondition(tokens, **kwargs):
      if len(tokens) == 0:
         return None # empty token list
      try:
         return conditions[tokens[0].lower()](tokens=tokens[1:],**kwargs)
      except KeyError:
         raise ValueError("condition/instruction {} not recognised.".format(tokens[0]))

   def __init__(self, pname = "NOPLAYER", tname = "NOTEAM", data = [], songname = "New Song", home = True):
      self.pname = pname
      self.tname = tname
      self.home = home
      self.songname = songname
      self.conditions = []
      self.instructions = []
      self.disabled = False
      self.startTime = 0
      self.endType = "loop"
      self.pauseType = "continue"
      for tokenStr in data:
         tokens = processTokens(tokenStr)
         condition = ConditionList.buildCondition(tokens, pname=self.pname, tname=self.tname, home=self.home)
         if condition.isInstruction():
            self.instructions.append(condition)
         else:
            self.conditions.append(condition)
      self.all = self.conditions + self.instructions

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

def loadsong(filename, vanthem = False):
   print("Attempting to load "+filename)
   filename = abspath(filename)
   if not ( isfile(filename) ):  
      raise Exception(filename+" not found.")
   source = vlc.MediaPlayer("file:///"+filename)
   if not vanthem:
      source.get_media().add_options("input-repeat=-1")
   return source

class ConditionPlayer (ConditionList):
   def __init__ (self, pname, tname, data, songname, home, song, type = "goalhorn"):
      ConditionList.__init__(self,pname,tname,data,songname,home)
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
      self.instruct()
   
   def instruct (self):
      for instruction in self.instructions:
         print("Preparing {} instruction".format(instruction))
         instruction.prep(self)

   def reloadSong (self):
      self.song = loadsong(self.songname, self.pname == "victory")
      self.instruct()

   def play (self):
      if self.fade is not None:
         print("Song played quickly after pause, cancelling fade.")
         thread = self.fade
         self.fade = None
         thread.join()
         
      self.song.play()
      if self.firstPlay:
         for instruction in self.instructionsStart:
            instruction.run(self)
         self.firstPlay = False
      if len(self.instructionsEnd) > 0:
         self.endChecker = threading.Thread(target=self.checkEnd)

   def adjustVolume (self, value):
      self.maxVolume = int(value)
      self.song.audio_set_volume(self.maxVolume)

   def pause (self):
      if self.type == "goalhorn" or (self.type in settings.fade and settings.fade[self.type]):
         print("Fading out {}.".format(self.songname))
         self.fade = threading.Thread(target=self.fadeOut)
         self.fade.start()
      else:
         print("Pausing {}.".format(self.songname))
         for instruction in self.instructionsPause:
            instruction.run(self)
         self.song.pause()
   
   def checkEnd (self):
      while self.endChecker is not None:
         if self.song.get_media().get_state() == vlc.State.Ended:
            for instruction in self.instructionsEnd:
               instruction.run(self)
            self.endChecker = None

   def fadeOut (self):
      i = 100
      while i > 0:
         if self.fade == None:
            break
         self.song.audio_set_volume(i)
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
      else:
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
