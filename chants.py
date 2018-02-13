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
         pass
      if awayParsed is not None:
         self.awayChants = awayParsed
      else:
         pass
      self.startChants = False
      self.activeChant = None
      self.goalDelay = False
      self.done = False
      self.timeEvent = Event()
      self.time = -1
      # locks for thread safety, and to prevent out-of-order event execution
      # per my standard convention please make sure to acquire nested locks in the order given here to prevent deadlock
      self.locks = {
         "event" : Lock(),
         "active" : Lock()
      }
      super().__init__(*args, **kwargs)

   def handlesEvent (self, eventType):
      handled = set(["Goal", "Own Goal", "Clock Started", "Clock Stopped", "Stats Found", "Player Sub", "Card"])
      return eventType in handled

   def handleGoalEvent (self, event):
      with self.locks["event"]:
         self.goal()
         self.startChants = False
         # time update
         self.time = event.gameMinute
         if self.time > self.times[0]:
            self.timeEvent.set()

   def handleOwnGoalEvent (self, event):
      with self.locks["event"]:
         self.goal()
         self.startChants = False
         # time update
         self.time = event.gameMinute
         if self.time > self.times[0]:
            self.timeEvent.set()

   def handleClockStartedEvent (self, event):
      with self.locks["event"]:
         if self.goalDelay == True:
            wait(settings.chants["goalDelay"])
            self.goalDelay = False
         self.startChants = True
         # time update
         self.time = event.gameMinute
         if len(self.times) > 0 and self.time > self.times[0]:
            self.timeEvent.set()

   def handleClockStoppedEvent (self, event):
      # time update
      with self.locks["event"]:
         self.startChants = False
         self.time = event.gameMinute
         if len(self.times) > 0 and self.time > self.times[0]:
            self.timeEvent.set()

   def handleStatsFoundEvent (self, event):
      # time update
      self.time = event.gameMinute
      Thread(target=self.mainLoop,daemon=True).start()

   def handleStatsLostEvent (self, event):
      self.done = True
      self.timeEvent.set()

   def handlePlayerSubEvent (self, event):
      # time update
      self.time = event.gameMinute

   def mainLoop (self):
      self.times = []
      self.timeEvent.clear()
      chantsPerTeam = settings.chants["perTeam"]
      # get approximate times for chants
      for i in range(2*chantsPerTeam):
         self.times.append(random.randint(settings.chants["minimum"], settings.chants["maximum"]))
      # sort them
      self.times.sort()
      # get team indicators
      teams = ["H" if x < chantsPerTeam else "A" for x in range(2*chantsPerTeam)]
      # shuffle them
      random.shuffle(teams)
      while len(self.times) > 0:
         # next chant happens at the first time
         nextChant = self.times[0]
         if self.time < nextChant:
            wait = (nextChant-self.time)*settings.gameMinute
            self.timeEvent.wait(wait) # don't tell me
         self.timeEvent.clear()
         # if we've lost stats, don't bother
         if self.done:
            break
         # we must be at least this far if we've been using approximated time
         if self.time < nextChant:
            self.time = nextChant
         self.times.pop(0)
         team = teams.pop(0)
         if team == "H":
            self.playHome()
         else:
            self.playAway()
         # someone's chant didn't play

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

   def start (self, SENPAI):
      SENPAI.addListener(self.manager)

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

