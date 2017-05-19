import threading
from time import sleep

from rigdio_util import timeToSeconds

fadeTime = 3

class Condition:
   def __init__(self, pname, tname):
      self.pname = pname
      self.tname = tname

   def __str__(self):
      return "Always True"
   __repr__ = __str__

   def check(self, gamestate):
      """
         Checks if a condition is true or not.
         
         Arguments:
          - gamestate (GameState): state of the game.
      """
      return True

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
      return "If Goals "+self.comparison
   __repr__ = __str__

   def check(self, gamestate):
      goals = gamestate.player_goals(self.pname)
      return eval(str(goals)+self.comparison)

def NotCondition (Condition):
   def __init__(self, pname, tname, condition):
      Condition.__init__(self,pname,tname)
      self.condition = condition

   def __str__(self):
      return "Not "+str(self.condition)

   def __repr__(self):
      return "Not "+repr(self.condition)

   def check(self, gamestate):
      return not self.condition.check(gamestate)

class ComebackCondition (Condition):
   def __init__(self, pname, tname):
      Condition.__init__(self,pname,tname)
      self.home = None

   def check(self,gamestate):
      if self.home == None:
         self.home = (gamestate.home_name == self.tname)
      if self.home:
         return gamestate.home_score <= gamestate.away_score and gamestate.away_score > 0
      else:
         return gamestate.away_score <= gamestate.home_score and gamestate.home_score > 0

class OpponentCondition (Condition):
   def __init__(self,pname,tname,tokens):
      Condition.__init__(self,pname,tname)
      self.other = tokens[0].lower()
      self.home = None

   def check(self,gamestate):
      if self.home == None:
         self.home = (gamestate.home_name == self.tname)
      if self.home:
         return gamestate.away_name == self.other
      else:
         return gamestate.home_name == self.other

class ConditionList (Condition):
   def buildCondition(self, pname, tname, tokens, song):
      if ( tokens[0].lower() == "goals" ):
         return GoalCondition(pname,tname,tokens[1:])
      elif ( tokens[0].lower() == "not" ):
         return NotCondition(pname,tname,buildCondition(tokens[1:]))
      elif ( tokens[0].lower() == "comeback" ):
         return ComebackCondition(pname,tname)
      elif ( tokens[0].lower() == "opponent" ):
         return OpponentCondition(pname,tname,tokens[1:])
      elif ( tokens[0].lower() == "start" ):
         self.startTime = 1000*int(timeToSeconds(tokens[1]))

   def __init__(self, pname, tname, song, songname, data, goalhorn = True):
      self.conditions = []
      self.song = song
      self.songname = songname
      self.startTime = 0
      self.isGoalhorn = goalhorn
      for token in data:
         tokens = token.split()
         condition = self.buildCondition(pname, tname, tokens, self.song)
         if condition is not None:
            self.conditions.append(condition)
   
   def __str__(self):
      return str(self.conditions)+": "+self.songname

   def play (self):
      self.song.play()
      if self.startTime is not 0:
         self.song.set_time(self.startTime)
         self.startTime = 0

   def pause (self):
      if self.isGoalhorn:
         fade = threading.Thread(target=fadeOut,args=(self.song,))
         fade.start()
      else:
         self.song.pause()

   def check (self, gamestate):
      for condition in self.conditions:
         if not condition.check(gamestate):
            return False
      return True

def fadeOut (song):
   i = 100
   while i > 0:
      song.audio_set_volume(i)
      sleep(fadeTime/100)
      i -= 1
   song.pause()
   song.audio_set_volume(100)