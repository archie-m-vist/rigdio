class Player:
   def __init__ (self, name, playerId, *args, **kwargs):
      try:
         super().__init__(*args,**kwargs)
      except Exception as e:
         handleExtraneous("Player",e)
      self.name = name
      self.id = playerId

   def __str__ (self):
      return "{} ({})".format(self.name, self.id)

class TeamInfo:
   def __init__ (self, name, id, players, *args, **kwargs):
      # this catches any excess arguments, but allows the constructor to proceed
      try:
         super().__init__(*args,**kwargs)
      except Exception as e:
         handleExtraneous("TeamInfo",e)
      self.teamname = name
      self.teamid = id
      self.players = [Player(**player) for player in players]

   def IDFromName (self, name):
      return self.ids[name]

   def nameFromID (self, pid):
      return self.names[pid]

   def nameFromIndex (self, index):
      return self.players[index]["name"]

   def indexFromName (self, name):
      for i in range(len(self.players)):
         if self.players[i]["name"] == name:
            return i
      raise KeyError("No player with name {} on team {} [{}]".format(name,self.teamname,self.teamid))

   def IDFromIndex (self, index):
      return self.players[index]["playerId"]

   def indexFromID (self, pid):
      for i in range(len(self.players)):
         if self.players[i]["playerId"] == pid:
            return i
      raise KeyError("No player with ID {} on team {} [{}]".format(name,self.teamname,self.teamid))

   def __str__ (self):
      output = "{} ({})".format(self.teamname, self.teamid)
      return output