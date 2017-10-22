class UnloadSong (Exception):
   def __str__ (self):
      "This condition will never be true again; unload the associated song to save RAM.\
      If you see this message, a serious error has occured; contact the developer."

class PlayNextSong (Exception):
   def __str__ (self):
      "A ConditionList's instruction needs the next song available to be played.\
      If you see this message, a serious error has occurred; contact the developer."

class SongNotFound (Exception):
   def __init__ (self, pname):
      self.pname = pname

   def __str__ (self):
      return "No song was found matching current game state for player {}. No music will play.".format(self.pname)