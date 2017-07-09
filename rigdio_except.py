class UnloadSong (Exception):
   def __str__ (self):
      "This condition will never be true again; unload the associated song to save RAM.\
      If you see this message, a serious error has occured; contact the developer."

class PlayNextSong (Exception):
   def __str__ (self):
      "Raised when a ConditionList's instruction needs the next song available to be played.\
      If you see this message, a serious error has occurred; contact the developer."