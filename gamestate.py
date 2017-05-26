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

   def is_home (self, tname):
      return (self.home_name == tname)

   def team_name (self, home):
      if home:
         return self.home_name
      else:
         return self.away_name

   def opponent_name (self, home):
      if home:
         return self.away_name
      else:
         return self.home_name

   def team_score (self, home):
      if home:
         return self.home_score
      else:
         return self.away_score

   def opponent_score (self, home):
      if home:
         return self.away_score
      else:
         return self.home_score

   def player_goals (self, pname):
      if pname in self.scorers:
         return self.scorers[pname]
      else:
         return 0

   def clear (self):
      self.home_score = 0
      self.away_score = 0
      self.scorers = {}