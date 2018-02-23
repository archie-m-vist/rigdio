import time
import random
from config import settings
from threading import RLock
from senPy import SENPAIListener

class EventManager (SENPAIListener):
   events = set([
                  "Player Sub",
                  "Card",
                  "Own Goal"
               ])

   types = ["sub", "red", "yellow", "owngoal"]

   def __init__ (self, parsed = None, *args, **kwargs):
      super().__init__(*args, **kwargs)
      
      self.clips = {x:{} for x in EventManager.types}
      self.setClips(parsed)
      self.last = {event: -1 for event in EventManager.types}
      self.lock = RLock()

   def handlesEvent (self, eventName):
      return eventName in EventManager.events

   def handlePlayerSubEvent (self, event):
      with self.lock:
         player = event.playerIn.name.upper()
         etype = "sub"
         etime = event.gameMinute
         self.checkAndPlay(player,etype,etime)

   def handleCardEvent (self, event):
      with self.lock:
         player = event.player.name.upper()
         etype = event.card.lower()
         etime = event.gameMinute
         self.checkAndPlay(player,etype,etime)

   def handleOwnGoalEvent (self, event):
      with self.lock:
         player = event.player.name.upper()
         etype = "owngoal"
         etime = event.gameMinute
         self.checkAndPlay(player,etype,etime)

   def checkAndPlay (self, player, etype, etime):
      with self.lock:
         clips = self.clips[etype]
         if etime > self.last[etype] and player in clips:
            random.shuffle(clips[player])
            song = clips[player][0]
            song.play()
            self.last[etype] = etime

   def setClips (self, parsed):
      self.clips = {x:{} for x in EventManager.types}
      if parsed is None:
         return
      for key in parsed.keys():
         self.clips[key] = {}
         for clist in parsed[key]:
            player = clist.pname.upper()
            if player not in self.clips[key]:
               self.clips[key][player] = []
            self.clips[key][player].append(clist)

class EventController:
   def __init__ (self, home=None, away=None):
      self.home = EventManager(home)
      self.away = EventManager(away)
      self.registered = False

   def setHome (self, parsed):
      self.home.setClips(parsed)
      print("Home team event clips ready.")

   def setAway (self, parsed):
      self.away.setClips(parsed)
      print("Away team event clips ready.")

   def start (self, SENPAI):
      if not self.registered:
         SENPAI.addListener(self.home)
         SENPAI.addListener(self.away)
         self.registered = True