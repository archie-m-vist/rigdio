from threading import RLock, Thread, Event
from config import settings
from senPy import SENPAIListener
from time import sleep
import random

class ChantPlayerManager (SENPAIListener):
   def __init__ (self, *args, homeFilename = None, awayFilename = None, homeParsed = None, awayParsed = None, **kwargs):
      # process home chants
      if homeParsed is not None:
         self.homeChants = homeParsed
      else:
         self.homeChants = None
      # process away chants
      if awayParsed is not None:
         self.awayChants = awayParsed
      else:
         self.awayChants = None
      # set to the currently playing chant, None if no chant is playing
      self.activeChant = None
      # times at which to play chants; randomly generated on first ClockUpdatedEvent
      self.times = None
      # target volume of chants, from 0 (muted) to 100 (full volume). Adjusted by slider.
      self.targetVolume = 100
      # queue for chants with overlapping times
      self.queue = []
      # used to check if we've slept enough after a chant ends to start a queued chant
      self.slept = True
      # Thread safety lock. If you don't know what this is don't change anything involving it.
      self.lock = RLock()
      # Pass anything else to superclass.
      super().__init__(*args, **kwargs)

   def handlesEvent (self, eventType):
      return eventType in set(["Clock Updated", "Goal"])

   def generateTimes (self, extra):
      self.times = []
      # regular time
      if not extra:
         # number of chants fixed in first half
         countFirst = settings.chants["perTeam"]["firstHalf"]
         # number of chants fixed in second half
         countSecond = settings.chants["perTeam"]["secondHalf"]
         # number of chants which could be in either half
         countFree = settings.chants["perTeam"]["free"]
         # generate chant times
         firstHalf = settings.chants["times"]["firstHalf"]
         secondHalf = settings.chants["times"]["secondHalf"]
         for i in range(countFirst):
            self.times.append((random.randint(firstHalf[0], firstHalf[1]), "H"))
            self.times.append((random.randint(firstHalf[0], firstHalf[1]), "A"))
         for i in range(countSecond):
            self.times.append((random.randint(secondHalf[0], secondHalf[1]), "H"))
            self.times.append((random.randint(secondHalf[0], secondHalf[1]), "A"))
         for i in range(countFree):
            target = random.choice([firstHalf, secondHalf])
            self.times.append((random.randint(target[0], target[1]), "H"))
            # home and away might be in different halves
            target = random.choice([firstHalf, secondHalf])
            self.times.append((random.randint(target[0], target[1]), "A"))
      # extra time
      else:
         count = settings.chants["perTeam"]["extra"]
         firstExtra = settings.chants["times"]["firstExtra"]
         secondExtra = settings.chants["times"]["secondExtra"]
         for i in range(count):
            target = random.choice([firstExtra, secondExtra])
            self.times.append((random.randint(target[0], target[1]), "H"))
            target = random.choice([firstExtra, secondExtra])
            self.times.append((random.randint(target[0], target[1]), "A"))
      self.times.sort(key=lambda entry: entry[0])
      # stop simultaneous chants deleting each other
      for i in range(len(self.times)-1):
         if self.times[i+1][0] <= self.times[i][0]:
            self.times[i+1] = (self.times[i][0]+1,self.times[i+1][1])
      print("Chant times:",self.times)

   def handleClockUpdatedEvent (self, event):
      with self.lock:
         if self.times is None:
            # generate times for regulation or extra time, as appropriate
            self.generateTimes(event.gameMinute > 90)
         # check if a chant can play:
         ## times must be generated
         ## game minute must match the time
         ## no chants in stoppage time
         if self.times is not None:
            minute = int(event.gameMinute)
            # if for whatever reason a chant should've played but hasn't, pop en masse and add to queue
            while minute > self.times[0][0]:
               team = self.times.pop(0)[1]
               if team == "H":
                  self.playHome()
               else:
                  self.playAway()
            # make sure the chants are playing at the correct times
            if minute == self.times[0][0] and event.injuryMinute is None:
               # pop team identifier from next chant; H for home, A for away
               team = self.times.pop(0)[1]
               # check identifier and play appropriate chant
               if team == "H":
                  self.playHome()
               else:
                  self.playAway()
            # if:
            ## no new chant can play (see above)
            ## no chant is playing
            ## a queued chant exists
            ## we've waited the minimum time since the last chant played
            # we play the queued chant now
            elif self.activeChant is None and len(self.queue) > 0 and self.slept:
               self.playQueued()

         # last game minute; reset times list
         if int(event.gameMinute) == 90 or int(event.gameMinute) == 120:
            self.times = None

   def handleGoalEvent (self, event):
      with self.lock:
         if self.activeChant is not None:
            self.activeChant.pause(fade=settings.chants["goalFade"])
            self.activeChant = None
            self.goal = True

   def adjustVolume (self, value):
      self.targetVolume = value
      with self.lock:
         if self.activeChant is not None:
            self.activeChant.adjustVolume(value)

   def playHome (self, manual = False):
      with self.lock:
         if self.homeChants is None or len(self.homeChants) == 0:
            print("No chant to play for away team.")
            return
         random.shuffle(self.homeChants);
         chant = self.homeChants.pop()
         self.playOrQueue(chant)
         if settings.chants["repeats"] or manual:
            self.homeChants.append(chant)

   def playAway (self, manual = False):
      with self.lock:
         if self.awayChants is None or len(self.awayChants) == 0:
            print("No chant to play for away team.")
            return
         random.shuffle(self.awayChants);
         chant = self.awayChants.pop()
         self.playOrQueue(chant)
         if settings.chants["repeats"] or manual:
            self.awayChants.append(chant)

   def playOrQueue (self, chant):
      with self.lock:
         if not self.slept or self.activeChant is not None:
            print("Chant clash; adding chant {} to queue.".format(chant.songname))
            self.queue.append(chant)
         else:
            self.activeChant = chant
            self.activeChant.onEnd(self.chantDone)
            self.activeChant.play()
            self.activeChant.adjustVolume(self.targetVolume)

   def playQueued (self):
      with self.lock:
         chant = self.queue.pop(0)
         print("Playing chant {} from queue.".format(chant.songname))
         # this should never re-queue a chant, since this is called directly from chantDone
         # (and thus should never yield the lock) but we call playOrQueue just in case
         # something strange happens and an un-queued chant starts playing despite this
         self.playOrQueue(chant)

   def chantDone (self, event):
      with self.lock:
         # activeChant will only be None during chantDone if a GoalEvent was handled
         # in this case we don't want to do anything on chantDone:
         ## there's nothing to log since the call to pause() already logs the file stopping
         ## if we play a queued chant, it'll interrupt goalhorns
         if self.activeChant is not None:
            print("Chant {} concluded.".format(self.activeChant.songname))
            self.activeChant = None
            if len(self.queue) > 0:
               sleep(settings.chants["delay"])
               self.slept = True

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
      else:
         print("No chants received for home team.")
         self.manager.homeChants = None

   def setAway (self, filename=None, parsed=None):
      if parsed is not None:
         self.manager.awayChants = parsed
      else:
         print("No chants received for away team.")
         self.manager.awayChants = None

   def playHome (self):
      Thread(target=self.manager.playHome,daemon=True).start()

   def playAway (self):
      Thread(target=self.manager.playAway,daemon=True).start()

   def adjustVolume (self, value):
      self.manager.adjustVolume(value)

