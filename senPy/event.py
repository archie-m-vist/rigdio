from .data import Player, TeamInfo

def handleExtraneous (cname, error):
   print("Non-fatal exception creating {} object (probably extraneous JSON):\n   {}".format(cname,error))

class Event:
   """
      General Python implementation of SEN:P-AI Event object.
   """
   def __init__ (self, event, timestamp, *args, **kwargs):
      """
         Constructor.
      """
      # this catches any excess arguments, but allows the constructor to proceed
      try:
         super().__init__(*args,**kwargs)
      except Exception as e:
         handleExtraneous("Event",e)
      self.timestamp = timestamp
      self.event = event

class MatchEvent (Event):
   def __init__ (self, gameMinute, injuryMinute, *args, **kwargs):
      super().__init__(*args, **kwargs)
      self.gameMinute = gameMinute
      self.injuryMinute = injuryMinute

class TeamsChangedEvent (Event):
   def __init__ (self, home, away, *args, **kwargs):
      super().__init__(*args, **kwargs)
      self.home = TeamInfo(**home)
      self.away = TeamInfo(**away)

   def __str__ (self):
      return "Teams Changed\n   Home: {}\n   Away: {}".format(self.home,self.away)

class ClockEvent (Event):
   def __init__ (self, gameMinute, injuryMinute = None, *args, **kwargs):
      super().__init__(*args, **kwargs)
      self.gameMinute = gameMinute
      self.injuryMinute = injuryMinute

class GoalEvent (ClockEvent):
   def __init__ (self, scorer, team, assister = None, *args, **kwargs):
      super().__init__(*args,**kwargs)
      self.scorer = Player(**scorer)
      self.assister = Player(**assister) if assister is not None else None
      self.team = team

   def __str__ (self):
      output = "Goal scored by {} for {} team".format(self.scorer,self.team)
      if self.assister is not None:
         output += ", assisted by {}".format(self.assister)
      return output

class ClockStartedEvent (ClockEvent):
   def __init__ (self, *args, **kwargs):
      super().__init__(*args,**kwargs)
   
   def __str__ (self):
      output = "Clock Started: {:.3f} Minutes".format(self.gameMinute)
      if self.injuryMinute is not None:
         output += ", {:.3f} Injury".format(self.injuryMinute)
      return output

class ClockStoppedEvent (ClockEvent):
   def __init__ (self, *args, **kwargs):
      super().__init__(*args,**kwargs)
   
   def __str__ (self):
      output = "Clock Stopped: {:.3f} Minutes".format(self.gameMinute)
      if self.injuryMinute is not None:
         output += ", {:.3f} Injury".format(self.injuryMinute)
      return output

class StatsFoundEvent (ClockEvent):
   def __init__ (self, homeScore, awayScore, *args, **kwargs):
      super().__init__(*args,**kwargs)
      self.homeScore = homeScore
      self.awayScore = awayScore
   
   def __str__ (self):
      return "Stats Found"

class StatsLostEvent (ClockEvent):
   def __init__ (self, *args, **kwargs):
      super().__init__(*args,**kwargs)

   def __str__ (self):
      return "Stats Lost"

class PlayerSubEvent (ClockEvent):
   def __init__ (self, playerIn, team, *args, **kwargs):
      super().__init__(*args, **kwargs)
      self.player = Player(**playerIn)
      self.team = team

   def __str__ (self):
      return "Player In: {} for {}".format(self.player, self.team)

class CardEvent (ClockEvent):
   def __init__ (self, player, card, team, *args, **kwargs):
      super().__init__(*args, **kwargs)
      self.player = Player(**player)
      self.card = card
      self.team = team
   
   def __str__ (self):
      return "Card: {} on {} for {}".format(self.card, self.player, self.team)

class OwnGoalEvent (ClockEvent):
   def __init__ (self, player, team, *args, **kwargs):
      super().__init__(*args, **kwargs)
      self.player = Player(**player)
      self.team = team

   def __str__ (self):
      return "Own Goal: {} for {}.".format(self.player, self.team)

# add new event types above this line, and add them to the dict

"""Provides a list of event objects by their SENPAI API type."""
eventTypes = {
   "Teams Changed" : TeamsChangedEvent,
   "Goal" : GoalEvent,
   "Clock Started" : ClockStartedEvent,
   "Clock Stopped" : ClockStoppedEvent,
   "Stats Found" : StatsFoundEvent,
   "Stats Lost" : StatsLostEvent,
   "Card" : CardEvent,
   "Player Sub" : PlayerSubEvent,
   "Own Goal" : OwnGoalEvent
}

def buildEvent (data):
   """
      Takes a JSON dictionary representing a SEN:P-AI event, and converts it to an appropriate Python object.
   """
   # SEN:P-AI objects 
   if "type" not in data:
      raise ValueError("handleEvent() requires SEN:P-AI object as Python dict.")
   # handleEvent is only concerned with Event objects; if and when others are added they will have their own handlers.
   if data["type"] != "Event":
      raise ValueError("handleEvent() requires SEN:P-AI Event object; got {} object.".format(data["Type"]))
   # remove type from dict, since it's served its purpose
   del data["type"]
   # try and build event object
   try:
      # if we find it, invoke the constructor and return it
      return eventTypes[data["event"]](**data)
   # if no event handler exists for this type, print it to console and move on
   except KeyError:
      print("no handler for event type {}.".format(data["event"]))
      return None