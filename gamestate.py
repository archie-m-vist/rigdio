class GameState:
   def __init__ (self, widget = None):
      self.home_score = 0
      self.away_score = 0
      self.home_name = "HOME"
      self.away_name = "AWAY"
      self.home_scorers = {}
      self.away_scorers = {}
      self.widget = widget

   def score (self, pname, home):
      print("Goal scored by {} on {} team.".format(pname, "home" if home else "away"))
      if home:
         self.home_score += 1
         if pname in self.home_scorers:
            self.home_scorers[pname] += 1
         else:
            self.home_scorers[pname] = 1
      else:
         self.away_score += 1
         if pname in self.away_scorers:
            self.away_scorers[pname] += 1
         else:
            self.away_scorers[pname] = 1
      # update scoreboard
      if self.widget is not None:
         self.widget.updateScore()

   def is_home (self, tname):
      """Checks if a team is at home. WARNING: Breaks in mirror matches (always says true)."""
      return (self.home_name == tname)

   def team_name (self, home):
      return self.home_name if home else self.away_name

   def opponent_name (self, home):
      return self.away_name if home else self.home_name

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

   def player_goals (self, pname, home):
      scorers = self.home_scorers if home else self.away_scorers
      if pname in scorers:
         return scorers[pname]
      else:
         return 0

   def clear (self):
      self.home_score = 0
      self.away_score = 0
      self.scorers = {}