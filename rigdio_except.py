class UnloadSong (Exception):
   def __str__ (self):
      "This condition will never be true again; unload the associated song to save RAM.\
      If you see this message, a serious error has occured; contact the developer."