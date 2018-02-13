from threading import Lock

class GameState:
   """
      Class storing game information.

      All GameState methods are threadsafe, except for anything involving instance. As such, use these rather than directly accessing variables where possible.
   """

   def __init__ (self, widget = None, instance = None):
      # score for home team
      self.home_score = 0
      # score for away team
      self.away_score = 0
      # name of home team
      self.home_name = "HOME"
      # name of away team
      self.away_name = "AWAY"
      # dict of player name : score for home team
      self.home_scorers = {}
      # dict of player name : score for away team
      self.away_scorers = {}
      # points back to main program
      self.instance = instance
      # score widget on main window
      self.widget = widget
      # type of game, set from dropdown in main window
      self.gametype = "standard"
      # time of a goal; used for non-SENPAI TimeCondition objects
      self.time = None
      # used for undo semantics
      self.lastPname = None
      # mutexes used for thread safety
      # to avoid hardlocking, if multiple mutexes must be nested, it is assumed the function will unlock them in the order listed here
      self.mutex = {
         "undo" : Lock(),
         "home" : Lock(),
         "away" : Lock(),
         "names" : Lock(),
         "flags" : Lock()
      }

   def undoLast (self):
      with self.mutex["undo"]:
         if self.lastPname == None:
            return
         if self.lastHome:
            with self.mutex["home"]:
               self.home_score -= 1
               self.home_scorers[self.lastPname] -= 1
         else:
            with self.mutex["away"]:
               self.away_score -= 1
               self.away_scorers[self.lastPname] -= 1
         self.lastPname = None
         self.widget.updateScore()

   def score (self, pname, home, automatic = False):
      """Scores a goal for player pname, on home team if home is True, otherwise away team."""
      # log goal
      print("Goal scored by {} on {} team.".format(pname, "home" if home else "away"))
      # save last play data for undo, in case of manual goals
      if not automatic:
         with self.mutex["undo"]:
            self.lastPname = pname
            self.lastHome = home
      # update home team score
      if home:
         with self.mutex["home"]:
            self.home_score += 1
            if pname in self.home_scorers:
               self.home_scorers[pname] += 1
            else:
               self.home_scorers[pname] = 1
      # update away team score
      else:
         with self.mutex["away"]:
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
      with self.mutex["names"]:
         return (self.home_name == tname)

   def team_name (self, home):
      with self.mutex["names"]:
         return self.home_name if home else self.away_name

   def opponent_name (self, home):
      with self.mutex["names"]:
         return self.away_name if home else self.home_name

   def team_score (self, home):
      if home:
         with self.mutex["home"]:
            return self.home_score
      else:
         with self.mutex["away"]:
            return self.away_score

   def opponent_score (self, home):
      if home:
         with self.mutex["away"]:
            return self.away_score
      else:
         with self.mutex["home"]:
            return self.home_score

   def team_scorers (self, home):
      if home:
         with self.mutex["home"]:
            return self.home_scorers
      else:
         with self.mutex["away"]:
            return self.away_scorers

   def opponent_scorers (self, home):
      if home:
         with self.mutex["away"]:
            return self.away_scorers
      else:
         with self.mutex["home"]:
            return self.home_scorers

   def player_goals (self, pname, home):
      if home:
         with self.mutex["home"]:
            if pname in self.home_scorers:
               return self.home_scorers["pname"]
            else:
               return 0
      else:
         with self.mutex["away"]:
            if pname in self.home_scorers:
               return self.home_scorers["pname"]
            else:
               return 0

   def clear (self):
      with self.mutex["home"]:
         with self.mutex["away"]:
            self.home_score = 0
            self.away_score = 0
            self.home_scorers = {}
            self.away_scorers = {}
            self.clearButtonFlags()

   def clearButtonFlags (self):
      with self.mutex["flags"]:
         self.time = None