import threading
from time import sleep
from os.path import basename

from rigdio_util import timeToSeconds

fadeTime = 3

class Condition:
   null = "nullCond"

   def __init__(self, pname, tname, home = True):
      self.pname = pname
      self.tname = tname
      self.home = home

   def __str__(self):
      return Condition.null
   __repr__ = __str__

   def check(self, gamestate):
      """
         Checks if a condition is true or not.
         
         Arguments:
          - gamestate (GameState): state of the game.
      """
      return True

   def isInstruction (self):
      """
         Checks if something is a Condition or an Instruction. There is no need to override this.

         Return:
          - <code>True</code> if the object is an Instruction, <code>False</code> if the object is a Condition.
      """
      return False

   def type (self):
      return str(self).split(" ")[0]

   def tokens (self):
      """
         Gives this Condition as a list of tokens, EXCLUDING the type of the condition.

         In essence, these are the tokens passed to the constructor.
      """
      return str(self).split(" ")[1:]

class ArithCondition (Condition):
   desc = """Superclass for all conditions that evaluate an arithmetic expression."""

   def check (self, gamestate):
      args = self.args(gamestate)
      return eval(self.comparison.format(*args))

class GoalCondition (ArithCondition):
   desc = """Plays when the number of goals this player has scored meet the condition."""

   def __init__(self, pname, tname, tokens, home = True):
      Condition.__init__(self,pname,tname,home)
      operators = ["<", ">", "<=", ">=", "=="]
      if tokens[0] == "=":
         tokens[0] = "=="
      if tokens[0] not in operators:
         raise Exception("invalid GoalCondition operator "+tokens[0]+"; valid operators are "+operators)
      self.comparison = "{} " + tokens[0]+" "+tokens[1]
   
   def __str__(self):
      return self.comparison.format("goals")
   __repr__ = __str__

   def args (self, gamestate):
      return (gamestate.player_goals(self.pname,self.home),)

class NotCondition (Condition):
   desc = """Plays when the given condition is false."""

   def __init__(self, pname, tname, tokens = [], home = True, condition = None):
      Condition.__init__(self,pname,tname,home)
      if condition is None:
         self.condition = ConditionList.buildCondition(pname,tname,tokens,home)
      else:
         self.condition = condition

   def __str__(self):
      return "not {}".format(str(self.condition))

   def __repr__(self):
      return "not {}".format(repr(self.condition))

   def check(self, gamestate):
      return not self.condition.check(gamestate)

class ComebackCondition (Condition):
   desc = """Plays when the team was behind prior to this goal being scored. Equivalent to gd <= 0."""

   def __init__(self, pname, tname, tokens, home = True):
      Condition.__init__(self,pname,tname,home)

   def check(self,gamestate):
      return gamestate.team_score(self.home) <= gamestate.opponent_score(self.home) and gamestate.opponent_score(self.home) > 0

   def __str__(self):
      return "comeback"
   __repr__ = __str__

class OpponentCondition (Condition):
   desc = """Plays when the opponent is one of the listed teams (separated by spaces, exclude slashes from ends)."""

   def __init__(self,pname,tname,tokens, home = True):
      Condition.__init__(self,pname,tname,home)
      self.others = [x.lower() for x in tokens]

   def check(self,gamestate):
      return gamestate.opponent_name(self.home) in self.others

   def __str__(self):
      return "opponent {}".format(" ".join(self.others))
   __repr__ = __str__

class FirstCondition (Condition):
   desc = """Plays if this is the first goal that the team has scored in this match."""
   
   def __init__ (self, pname, tname, tokens, home = True):
      Condition.__init__(self,pname,tname,home)

   def check(self, gamestate):
      return gamestate.team_score(self.home) == 1

   def __str__(self):
      return "first"
   __repr__ = __str__

class LeadCondition (GoalCondition):
   desc = """Plays if the goal difference (yourteam - theirteam) meets the given condition."""

   def __init__ (self, pname, tname, tokens, home = True):
      GoalCondition.__init__(self,pname,tname,tokens,home)

   def args(self, gamestate):
      gd = gamestate.team_score(self.home) - gamestate.opponent_score(self.home)
      return (gd,)

   def __str__(self):
      return self.comparison.format("lead")
   __repr__ = __str__

class MatchCondition (Condition):
   desc = """Plays if the match is the corresponding type (standard, knockouts, final)."""

   def __init__ (self, pname, tname, tokens, home = True):
      Condition.__init__(self,pname,tname,home)
      self.type = tokens[0].lower()

   def check (self, gamestate):
      return gamestate.gametype == self.type

   def __str__(self):
      return "match {}".format(self.type)
   __repr__ = __str__

class HomeCondition (Condition):
   desc = """Plays if the team is at home. (Use 'not home' for away.)"""

   def __init__(self, pname, tname, tokens, home = True):
      Condition.__init__(self,pname,tname,home)

   def check (self, gamestate):
      return self.home

   def __str__(self):
      return "home"
   __repr__ = __str__

class Instruction:
   """
      Class used for something which modifies a ConditionPlayer rather than determining when it will play.

      This is a purely internal distinction; Instruction and Condition objects are manipulated and created the same ways.
   """
   def isInstruction (self):
      return True

   """
      Applies this instruction to a given media player object. Returns True on success or False on failure.
   """
   def run (self, player):
      return True

   def __str__(self):
      return "nullInst"
   __repr__ = __str__

   def type (self):
      return str(self).split(" ")[0]

   def tokens (self):
      """
         Gives this Instruction as a list of tokens, EXCLUDING the type of the condition.

         In essence, these are the tokens passed to the constructor.
      """
      return str(self).split(" ")[1:]

class StartInstruction (Instruction):
   desc = """Starts the file at the given time (in min:sec format)."""

   def __init__ (self, pname, tname, tokens, home = True):
      timestring = tokens[0]
      self.rawTime = timestring
      self.startTime = 1000*int(timeToSeconds(timestring))

   def run (self, player):
      player.startTime = self.startTime

   def __str__(self):
      return "start {}".format(self.rawTime)
   __repr__ = __str__

class PauseInstruction (Instruction):
   desc = """Specify action taken when goalhorn is paused."""

   def __init__ (self, pname, tname, tokens, home = True):
      types = ["continue", "restart"]
      if tokens[0] not in types:
         raise ValueError("Unrecognised pause type (allowed values: {}).".format(", ".join(types)))
      self.type = tokens[0]

   def run (self, player):
      player.pauseType = self.type

   def __str__(self):
      return "pause {}".format(self.type)
   __repr__ = __str__

conditions = {
   "goals" : GoalCondition,
   "comeback" : ComebackCondition,
   "first" : FirstCondition,
   "opponent" : OpponentCondition,
   "not" : NotCondition,
   "lead" : LeadCondition,
   "match" : MatchCondition,
   "home" : HomeCondition,
   "start" : StartInstruction,
   "pause" : PauseInstruction
}

class ConditionList:
   def buildCondition(pname, tname, tokens, home = True):
      if len(tokens) == 0:
         raise ValueError("Cannot build condition without tokens.")
      try:
         return conditions[tokens[0].lower()](pname,tname,tokens[1:],home)
      except KeyError:
         raise ValueError("condition/instruction {} not recognised.".format(tokens[0]))

   def __init__(self, pname, tname, data, songname, home = True):
      self.pname = pname
      self.tname = tname
      self.songname = songname
      self.conditions = []
      self.instructions = []
      self.startTime = 0
      self.pauseType = "continue"
      for token in data:
         tokens = token.split()
         condition = ConditionList.buildCondition(pname, tname, tokens, home)
         if condition.isInstruction():
            self.instructions.append(condition)
         else:
            self.conditions.append(condition)
      self.all = self.conditions + self.instructions

   def append (self, item):
      self.all.append(item)
      if item.isInstruction():
         self.instructions.append(item)
      else:
         self.conditions.append(item)
   
   def __str__(self):
      output = "{}".format(basename(self.songname))
      for condition in self.conditions:
         output = output + ";" + str(condition)
      for instruction in self.instructions:
         output = output + ";" + str(instruction)
      return output
   __repr__ = __str__

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

   def pop (self, index = 0):
      item = self.all.pop(index)
      if item.isInstruction():
         self.instructions.remove(item)
      else:
         self.conditions.remove(item)
      return item

   def check (self, gamestate):
      for condition in self.conditions:
         print("Checking {}".format(condition))
         if not condition.check(gamestate):
            return False
      return True

class ConditionPlayer (ConditionList):
   def __init__ (self, pname, tname, data, songname, home, song, goalhorn = True):
      ConditionList.__init__(self,pname,tname,data,songname,home)
      self.song = song
      self.isGoalhorn = goalhorn
      self.fade = None
      self.startTime = 0
      self.pauseType = "continue"
      for instruction in self.instructions:
         print(instruction)
         instruction.run(self)

   def play (self):
      if self.fade is not None:
         print("Song played quickly after pause, cancelling fade.")
         thread = self.fade
         self.fade = None
         thread.join()
      self.song.play()
      # StartInstruction necessary code
      if self.startTime is not 0:
         self.song.set_time(self.startTime)
         if self.pauseType != "restart":
            self.startTime = 0

   def pause (self):
      if self.isGoalhorn:
         print("Fading out {}.".format(self.songname))
         self.fade = threading.Thread(target=fadeOut,args=(self,))
         self.fade.start()
      else:
         print("Pausing {}.".format(self.songname))
         if self.pauseType == "restart":
            self.song.set_time(self.startTime)
         self.song.pause()
   

def fadeOut (player):
   i = 100
   while i > 0:
      if player.fade == None:
         break
      player.song.audio_set_volume(i)
      sleep(fadeTime/100)
      i -= 1
   if player.pauseType == "restart":
      player.song.set_time(player.startTime)
   player.song.pause()
   player.song.audio_set_volume(100)