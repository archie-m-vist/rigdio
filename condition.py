import threading
from time import sleep
from os.path import basename

from rigdio_util import timeToSeconds

fadeTime = 3

class Condition:
   def __init__(self, pname, tname):
      self.pname = pname
      self.tname = tname
      self.home = None

   def __str__(self):
      return "nullCond"
   __repr__ = __str__

   def check(self, gamestate):
      """
         Checks if a condition is true or not.
         
         Arguments:
          - gamestate (GameState): state of the game.
      """
      return True

   def isInstruction (self):
      return False


class GoalCondition (Condition):
   def __init__(self, pname, tname, tokens):
      Condition.__init__(self,pname,tname)
      operators = ["<", ">", "<=", ">=", "=="]
      if tokens[0] == "=":
         tokens[0] = "=="
      if tokens[0] not in operators:
         raise Exception("invalid GoalCondition operator "+tokens[0]+"; valid operators are "+operators)
      self.comparison = tokens[0]+" "+tokens[1]
   
   def __str__(self):
      return "goals {}".format(self.comparison)
   __repr__ = __str__

   def check(self, gamestate):
      goals = gamestate.player_goals(self.pname)
      return eval(str(goals)+self.comparison)

class NotCondition (Condition):
   def __init__(self, pname, tname, condition):
      if condition is None:
         raise ValueError("NotCondition requires a proper Condition object.")
      Condition.__init__(self,pname,tname)
      self.condition = condition

   def __str__(self):
      return "not {}".format(str(self.condition))

   def __repr__(self):
      return "not {}".format(repr(self.condition))

   def check(self, gamestate):
      return not self.condition.check(gamestate)

class ComebackCondition (Condition):
   def __init__(self, pname, tname):
      Condition.__init__(self,pname,tname)

   def check(self,gamestate):
      if self.home == None:
         self.home = (gamestate.home_name == self.tname)
      return gamestate.team_score(self.home) <= gamestate.opponent_score(self.home) and gamestate.opponent_score(self.home) > 0

   def __str__(self):
      return "comeback"
   __repr__ = __str__

class OpponentCondition (Condition):
   def __init__(self,pname,tname,tokens):
      Condition.__init__(self,pname,tname)
      self.other = tokens[0].lower()

   def check(self,gamestate):
      if self.home == None:
         self.home = (gamestate.home_name == self.tname)
      return gamestate.opponent_name(self.home) == self.other

   def __str__(self):
      return "opponent {}".format(self.other)
   __repr__ = __str__

class FirstCondition (Condition):
   def __init__(self, pname, tname):
      Condition.__init__(self,pname,tname)
   
   def check (self, gamestate):
      if self.home == None:
         self.home = gamestate.is_home(self.tname)
      return gamestate.team_score(self.home) == 1

   def __str__(self):
      return "first"
   __repr__ = __str__

class Instruction:
   """
      Class used for something which modifies a ConditionPlayer without being a condition itself.
   """
   def isInstruction (self):
      return True

   """
      Applies this instruction to the player. Returns True on success or False on failure.
   """
   def run (self, player):
      return True

   def __str__(self):
      return "nullInst"
   __repr__ = __str__

class StartInstruction (Instruction):
   def __init__ (self, timestring):
      self.rawTime = timestring
      self.startTime = 1000*int(timeToSeconds(timestring))

   def run (self, player):
      player.song.set_time(self.startTime)
      return True

   def __str__(self):
      return "start {}".format(self.rawTime)

class ConditionList (Condition):
   def buildCondition(self, pname, tname, tokens):
      if ( tokens[0].lower() == "goals" ):
         return GoalCondition(pname,tname,tokens[1:])
      elif ( tokens[0].lower() == "not" ):
         try:
            return NotCondition(pname,tname,self.buildCondition(pname,tname,tokens[1:]))
         except ValueError:
            print("Bad condition type as NotCondition argument: {}".format(tokens[1]))
            return None
      elif ( tokens[0].lower() == "comeback" ):
         return ComebackCondition(pname,tname)
      elif ( tokens[0].lower() == "opponent" ):
         return OpponentCondition(pname,tname,tokens[1:])
      elif ( tokens[0].lower() == "first" ):
         return FirstCondition(pname,tname)
      # instructions
      elif ( tokens[0].lower() == "start" ):
         return StartInstruction(tokens[1])
      return None

   def __init__(self, pname, tname, data, songname):
      self.conditions = []
      self.instructions = []
      self.startTime = 0
      self.songname = songname
      for token in data:
         tokens = token.split()
         condition = self.buildCondition(pname, tname, tokens)
         if condition.isInstruction:
            self.instructions.append(condition)
         else:
            self.conditions.append(condition)

   
   def __str__(self):
      output = "{}".format(basename(self.songname))
      for condition in self.conditions:
         output = output + ";" + str(condition)
      for instruction in self.instructions:
         output = output + ";" + str(instruction)
      return output
   __repr__ = __str__

   def __len__ (self):
      return len(self.conditions)

   def __iter__ (self):
      return self.conditions.__iter__()

   def __getitem__ (self, key):
      return self.conditions[key]

   def check (self, gamestate):
      for condition in self.conditions:
         if not condition.check(gamestate):
            return False
      return True

class ConditionPlayer (ConditionList):
   def __init__ (self, pname, tname, data, songname, song, goalhorn = True):
      ConditionList.__init__(self,pname,tname,data,songname)
      self.song = song
      self.isGoalhorn = goalhorn
      for instruction in self.instructions:
         instruction.run(self)

   def play (self):
      self.song.play()

   def pause (self):
      if self.isGoalhorn:
         fade = threading.Thread(target=fadeOut,args=(self.song,))
         fade.start()
      else:
         self.song.pause()
   

def fadeOut (song):
   i = 100
   while i > 0:
      song.audio_set_volume(i)
      sleep(fadeTime/100)
      i -= 1
   song.pause()
   song.audio_set_volume(100)