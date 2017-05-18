from rigdio_util import timeToSeconds

class Condition:
   def __init__(self, pname):
      self.pname = pname

   def __str__(self):
      return "Always True"
   __repr__ = __str__

   def check(self, gamestate):
      """
         Checks if a condition is true or not.
         
         Arguments:
          - gamestate (GameState):
      """
      return True

class GoalCondition (Condition):
   def __init__(self, pname, tokens):
      Condition.__init__(self,pname)
      operators = ["<", ">", "<=", ">=", "=="]
      if tokens[1] == "=":
         tokens[1] = "=="
      if tokens[1] not in operators:
         raise Exception("invalid GoalCondition operator "+tokens[1]+"; valid operators are "+operators)
      self.comparison = tokens[1]+" "+tokens[2]
   
   def __str__(self):
      return "If Goals "+self.comparison
   __repr__ = __str__

   def check(self, gamestate):
      goals = gamestate.player_goals(self.pname)
      return eval(str(goals)+self.comparison)

def NotCondition (Condition):
   def __init__(self, pname, condition):
      Condition.__init__(self,pname)
      self.condition = condition

   def __str__(self):
      return "Not "+str(self.condition)

   def __repr__(self):
      return "Not "+repr(self.condition)

   def check(self, gamestate):
      return not self.condition.check(gamestate)

class ConditionList (Condition):
   def buildCondition(self, pname, tokens, song):
      if ( tokens[0].lower() == "goals" ):
         return GoalCondition(pname,tokens)
      elif ( tokens[0].lower() == "not" ):
         return NotCondition(pname,buildCondition(tokens[1:]))
      elif ( tokens[0].lower() == "start" ):
         self.startTime = 1000*int(timeToSeconds(tokens[1]))

   def __init__(self, pname, song, songname, data):
      self.conditions = []
      self.song = song
      self.songname = songname
      self.startTime = 0
      for token in data:
         tokens = token.split()
         condition = self.buildCondition(pname, tokens, self.song)
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
      self.song.pause()

   def check (self, gamestate):
      for condition in self.conditions:
         if not condition.check(gamestate):
            return False
      return True