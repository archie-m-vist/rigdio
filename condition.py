class Condition:
   def __init__(self, pname):
      self.pname = pname

   def __str__(self):
      return "Always True"
   __repr__ = __str__

   def check(self, gamestate):
      return True

class GoalCondition (Condition):
   def __init__(self, pname, tokens):
      Condition.__init__(self,pname)
      operators = ["<", ">", "<=", ">=", "="]
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
   def buildCondition(pname, tokens):
      if ( tokens[0].lower() == "goals" ):
         return GoalCondition(pname,tokens)
      elif ( tokens[0].lower() == "not" ):
         return NotCondition(pname,buildCondition(tokens[1:]))

   def __init__(self, pname, song, songname, data):
      self.conditions = []
      self.song = song
      self.songname = songname
      for token in data:
         tokens = token.split()
         condition = ConditionList.buildCondition(pname, tokens)
         self.conditions.append(condition)
   
   def __str__(self):
      return str(self.conditions)+": "+self.songname

   def check (self, gamestate):
      for condition in self.conditions:
         if not condition.check(gamestate):
            return False
      return True