import threading
from time import sleep
from os.path import basename

from rigdio_util import timeToSeconds

fadeTime = 3

class Condition:
   null = "nullCond"

   def __init__(self, pname, tname):
      self.pname = pname
      self.tname = tname
      self.home = None

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

class GoalCondition (Condition):
   desc = """Plays when the number of goals this player has scored meet the condition."""

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
   desc = """Plays when the given condition is false."""

   def __init__(self, pname, tname, tokens = [], condition = None):
      Condition.__init__(self,pname,tname)
      if condition is None:
         self.condition = ConditionList.buildCondition(pname,tname,tokens)
      else:
         self.condition = condition

   def __str__(self):
      return "not {}".format(str(self.condition))

   def __repr__(self):
      return "not {}".format(repr(self.condition))

   def check(self, gamestate):
      return not self.condition.check(gamestate)

class ComebackCondition (Condition):
   desc = """Plays when the team was behind prior to this goal being scored."""

   def __init__(self, pname, tname, tokens):
      Condition.__init__(self,pname,tname)

   def check(self,gamestate):
      if self.home == None:
         self.home = (gamestate.home_name == self.tname)
      return gamestate.team_score(self.home) <= gamestate.opponent_score(self.home) and gamestate.opponent_score(self.home) > 0

   def __str__(self):
      return "comeback"
   __repr__ = __str__

class OpponentCondition (Condition):
   desc = """Plays when the opponent is one of the listed teams (separated by spaces, exclude slashes from ends)."""

   def __init__(self,pname,tname,tokens):
      Condition.__init__(self,pname,tname)
      self.others = [x.lower() for x in tokens]

   def check(self,gamestate):
      if self.home == None:
         self.home = (gamestate.home_name == self.tname)
      return gamestate.opponent_name(self.home) in self.others

   def __str__(self):
      return "opponent {}".format(" ".join(self.others))
   __repr__ = __str__

class FirstCondition (Condition):
   desc = """Plays if this is the first goal that the team has scored in this match."""

   def __init__(self, pname, tname,tokens):
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

   def __init__ (self, timestring):
      self.rawTime = timestring
      self.startTime = 1000*int(timeToSeconds(timestring))

   def run (self, player):
      player.song.set_time(self.startTime)
      return True

   def __str__(self):
      return "start {}".format(self.rawTime)

class ConditionList (Condition):
   def buildCondition(pname, tname, tokens):
      if len(tokens) == 0:
         return None
      elif ( tokens[0].lower() == "goals" ):
         return GoalCondition(pname,tname,tokens[1:])
      elif ( tokens[0].lower() == "not" ):
         try:
            return NotCondition(pname,tname,tokens[1:])
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
      self.pname = pname
      self.tname = tname
      self.songname = songname
      self.conditions = []
      self.instructions = []
      self.startTime = 0
      for token in data:
         tokens = token.split()
         condition = ConditionList.buildCondition(pname, tname, tokens)
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
         if not condition.check(gamestate):
            return False
      return True

class ConditionPlayer (ConditionList):
   def __init__ (self, pname, tname, data, songname, song, goalhorn = True):
      ConditionList.__init__(self,pname,tname,data,songname)
      self.song = song
      self.isGoalhorn = goalhorn
      self.fade = None
      for instruction in self.instructions:
         instruction.run(self)

   def play (self):
      if self.fade is not None:
         print("Song played quickly after pause, cancelling fade.")
         thread = self.fade
         self.fade = None
         thread.join()
      self.song.play()

   def pause (self):
      if self.isGoalhorn:
         print("Fading out {}.".format(self.songname))
         self.fade = threading.Thread(target=fadeOut,args=(self,))
         self.fade.start()
      else:
         print("Pausing {}.".format(self.songname))
         self.song.pause()
   

def fadeOut (player):
   i = 100
   while i > 0:
      if player.fade == None:
         break
      player.song.audio_set_volume(i)
      sleep(fadeTime/100)
      i -= 1
   player.song.pause()
   player.song.audio_set_volume(100)