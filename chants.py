from threading import Lock, Thread, Event
from config import settings
from condition import ConditionPlayer
from senPy import SENPAIListener
from time import sleep
import random

class ChantPlayerManager (SENPAIListener):
   def __init__ (self, *args, homeFilename = None, awayFilename = None, homeParsed = None, awayParsed = None, **kwargs):
      if homeParsed is not None:
         self.homeChants = homeParsed
      else:
         self.homeChants = None
      if awayParsed is not None:
         self.awayChants = awayParsed
      else:
         self.awayChants = None
      self.startChants = False
      self.activeChant = None
      self.goalDelay = False
      self.done = False
      self.timeEvent = Event()
      self.time = -1
      self.times = None
      self.targetVolume = 100
      # locks for thread safety, and to prevent out-of-order event execution
      # per my standard convention please make sure to acquire nested locks in the order given here to prevent deadlock
      self.locks = {
         "event" : Lock(),
         "active" : Lock(),
         "times" : Lock()
      }
      super().__init__(*args, **kwargs)

   def handlesEvent (self, eventType):
      print("Got",eventType)
      handled = set(["Goal", "Own Goal", "Clock Started", "Clock Stopped", "Stats Found", "Player Sub", "Card"])
      return eventType in handled

   def handleGoalEvent (self, event):
      with self.locks["event"]:
         self.goal()
         self.startChants = False
         # time update
         self.time = event.gameMinute
         self.timeEvent.set()

   def handleOwnGoalEvent (self, event):
      with self.locks["event"]:
         self.goal()
         self.startChants = False
         # time update
         self.time = event.gameMinute
         self.timeEvent.set()

   def handleClockStartedEvent (self, event):
      print("Started!",event.gameMinute)
      with self.locks["event"]:
         if self.goalDelay == True:
            wait(settings.chants["goalDelay"])
            self.goalDelay = False
         self.startChants = True
         # time update
         self.time = event.gameMinute
         self.timeEvent.set()

   def handleClockStoppedEvent (self, event):
      # time update
      with self.locks["event"]:
         self.startChants = False
         self.time = event.gameMinute
         self.timeEvent.set()

   def handleStatsFoundEvent (self, event):
      # time update
      self.time = event.gameMinute
      self.done = False
      Thread(target=self.mainLoop,daemon=True).start()

   def handleStatsLostEvent (self, event):
      self.done = True
      self.timeEvent.set()

   def handlePlayerSubEvent (self, event):
      # time update
      with self.locks["event"]:
         self.startChants = False
         self.time = event.gameMinute
         self.timeEvent.set()

   def handleCardEvent (self, event):
      with self.locks["event"]:
         self.startChants = False
         self.time = event.gameMinute
         self.timeEvent.set()

   def mainLoop (self):
      with self.locks["times"]:
         if self.times is not None:
            return
         self.times = []
      self.timeEvent.clear()
      chantsPerTeam = settings.chants["perTeam"]
      # get approximate times for chants
      for i in range(2*chantsPerTeam):
         self.times.append(random.randint(settings.chants["minimum"], settings.chants["maximum"]))
      # sort them
      self.times.sort()
      print("Chant target times:",self.times)
      # get team indicators
      teams = ["H" if x < chantsPerTeam else "A" for x in range(2*chantsPerTeam)]
      # shuffle them
      random.shuffle(teams)
      while len(self.times) > 0:
         # next chant happens at the first time
         nextTime = self.times.pop(0)
         oldTime = self.time
         while self.time < nextTime:
            wait = (nextTime-self.time)*settings.gameMinute
            print("Waiting for {} seconds to approximate chant play (target {}, recorded time {})".format(wait, nextTime, self.time))
            self.timeEvent.clear() # start wait fresh
            self.timeEvent.wait(wait) # don't tell me
            # if time hasn't changed since waiting, continue
            if self.time == oldTime:
               break
         self.timeEvent.clear()
         # if we've lost stats, don't bother
         if self.done:
            break
         # set time based on approximation
         if self.time < nextTime and self.time == oldTime:
            self.time = nextTime
         team = teams.pop(0)
         if team == "H":
            self.playHome()
         else:
            self.playAway()
      self.times = None

   def adjustVolume (self, value):
      self.targetVolume = value
      with self.locks["active"]:
         if self.activeChant is not None:
            self.activeChant.adjustVolume(value)

   def goal (self):
      with self.locks["active"]:
         if self.activeChant is not None:
            self.activeChant.pause(fade=settings.chants["goalFade"])
            self.startChants = False
            self.activeChant = None
            self.goal = True

   def playHome (self):
      while self.activeChant is not None or not self.startChants:
         sleep(settings.chants["delay"])
      with self.locks["active"]:
         if self.homeChants is None or len(self.homeChants) == 0:
            print("No chant to play for home team.")
            return
         random.shuffle(self.homeChants);
         self.activeChant = self.homeChants.pop()
         self.activeChant.onEnd(self.chantDone)
         print("Playing chant {} for home team.".format(self.activeChant.songname))
         self.activeChant.play()
         self.activeChant.adjustVolume(self.targetVolume)
         if settings.chants["repeats"]:
            self.homeChants.append(self.activeChant)

   def playAway (self):
      while self.activeChant is not None or not self.startChants:
         sleep(settings.chants["delay"])
      with self.locks["active"]:
         if self.awayChants is None or len(self.awayChants) == 0:
            print("No chant to play for away team.")
            return
         random.shuffle(self.awayChants);
         self.activeChant = self.awayChants.pop()
         self.activeChant.onEnd(self.chantDone)
         print("Playing chant {} for away team.".format(self.activeChant.songname))
         self.activeChant.play()
         self.activeChant.adjustVolume(self.targetVolume)
         if settings.chants["repeats"]:
            self.awayChants.append(self.activeChant)

   def chantDone (self, event):
      with self.locks["active"]:
         print("Chant {} concluded.".format(self.activeChant.songname))
         self.activeChant = None

class ChantManager:
   def __init__ (self):
      self.manager = ChantPlayerManager();
      self.registered = False

   def start (self, SENPAI):
      if not self.registered:
         SENPAI.addListener(self.manager)
         self.registered = True

   def setHome (self, filename=None, parsed=None):
      if parsed is not None:
         self.manager.homeChants = parsed

   def setAway (self, filename=None, parsed=None):
      if parsed is not None:
         self.manager.awayChants = parsed

   def playHome (self):
      Thread(target=self.manager.playHome,daemon=True).start()

   def playAway (self):
      Thread(target=self.manager.playAway,daemon=True).start()

   def adjustVolume (self, value):
      self.manager.adjustVolume(value)

