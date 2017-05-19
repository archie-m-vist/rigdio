class GameState:
   def __init__ (self):
      self.home_score = 0
      self.away_score = 0
      self.home_name = "HOME"
      self.away_name = "AWAY"
      self.scorers = {}

   def score (self, pname, home):
      if ( home == True ):
         self.home_score += 1
      else:
         self.away_score += 1

      if pname in self.scorers:
         self.scorers[pname] += 1
      else:
         self.scorers[pname] = 1

   def player_goals (self, pname):
      if pname in self.scorers:
         return self.scorers[pname]
      else:
         return 0

   def clear (self):
      self.home_score = 0
      self.away_score = 0
      self.home_name = "HOME"
      self.away_name = "AWAY"
      self.scorers = {}