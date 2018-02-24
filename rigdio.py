import sys
from os.path import isfile, join, abspath

from tkinter import *
import tkinter.filedialog as filedialog
import tkinter.messagebox as messagebox

from config import genCfg, settings

from condition import MatchCondition
from rigparse import parse
from gamestate import GameState
from songgui import *
from version import rigdio_version as version
from senPy import ThreadSENPAI, SENPAINotFound, SENPAIConnectionFailed, SENPAIPipeClosed
from rigdj_util import setMaxWidth
from chants import ChantManager
from event import EventController

from logger import startLog
if __name__ == '__main__':
   startLog("rigdio.log")
   print("rigdio {}".format(version))

class ScoreWidget (Frame):
   def __init__ (self, master, game):
      Frame.__init__(self,master)
      self.game = game
      # home/away team name labels
      self.homeName = StringVar()
      self.awayName = StringVar()
      self.updateLabels()
      Label(self, textvariable=self.homeName, font="-weight bold").grid(row=0,column=0)
      Label(self, text="vs.", font="-weight bold").grid(row=0,column=1)
      Label(self, textvariable=self.awayName, font="-weight bold").grid(row=0,column=2)
      # score tracker
      self.homeScore = IntVar()
      self.awayScore = IntVar()
      self.updateScore()
      Label(self, textvariable=self.homeScore).grid(row=1,column=0)
      Label(self, text="-").grid(row=1,column=1)
      Label(self, textvariable=self.awayScore).grid(row=1,column=2)

   def updateLabels (self):
      self.homeName.set("/{}/".format(self.game.home_name))
      self.awayName.set("/{}/".format(self.game.away_name))

   def updateScore (self):
      self.homeScore.set(self.game.home_score)
      self.awayScore.set(self.game.away_score)

class Rigdio (Frame):
   def __init__ (self, master):
      Frame.__init__(self, master)
      self.game = GameState(instance=self)
      self.home = None
      self.away = None
      # file menu
      Button(self, text="Load Home Team", command=self.loadFile, bg=settings.colours["home"]).grid(row=0, column=0)
      Button(self, text="Load Away Team", command=lambda: self.loadFile(False), bg=settings.colours["away"]).grid(row=0, column=2)
      # score widget
      self.scoreWidget = ScoreWidget(self, self.game)
      self.game.widget = self.scoreWidget
      self.scoreWidget.grid(row=0, column=1)
      # game type selector
      self.initGameTypeMenu().grid(row=1,column=1)
      # chant buttons
      self.chants = ChantManager()
      senpaiControls = Frame(self)
      Button(senpaiControls, text="Connect to SENPAI", command=self.activateSENPAI).pack()
      Label(senpaiControls, text="Chant Volume").pack()
      chantVolume = Scale(senpaiControls, from_=0, to=100, orient=HORIZONTAL, command=self.chants.adjustVolume, showvalue=0)
      chantVolume.set(100)
      chantVolume.pack()
      #manualChants = Frame(senpaiControls)
      #Label(manualChants, text="Manual Chants").grid(row=0,column=0,columnspan=2)
      #Button(manualChants, text="Home", command=self.chants.playHome, bg=settings.colours["home"]).grid(row=1,column=0)
      #Button(manualChants, text="Away", command=self.chants.playAway, bg=settings.colours["away"]).grid(row=1,column=1)
      #manualChants.pack()
      senpaiControls.grid(row=2, column=1)
      # events
      self.events = EventController()
      # undo (temporary)
      Button(self, text="Undo Last Goal", command=self.game.undoLast).grid(row=3, column=1)
      # SENPAI integration
      self.SENPAI = None

   def initGameTypeMenu (self):
      gameTypeMenu = Frame(self)
      gametypes = MatchCondition.types
      Label(gameTypeMenu, text="Match Type").pack()
      gametype = StringVar()
      gametype.set("Group")
      self.game.gametype = gametype.get().lower()
      menu = OptionMenu(gameTypeMenu, gametype, *gametypes, command=self.changeGameType)
      setMaxWidth(gametypes,menu)
      menu.pack()
      return gameTypeMenu

   def changeGameType (self, option):
      self.game.gametype = option.lower()

   def loadFile (self, home = True):
      f = filedialog.askopenfilename(filetypes = (("Rigdio export files", "*.4ccm"),("All files","*.*")))
      if f == "":
         # do nothing if cancel was pressed
         return
      elif isfile(f):
         print("Loading music instructions from {}.".format(f))
         try:
            tmusic, tname, events = parse(f,home=home)
         except AttributeError as e:
            messagebox.showerror("AttributeError on file load.","Did you download rigdio.exe instead of rigdio.7z? Make sure that the libVLC DLLs and plugins directory are present.")
            raise e
         # this will only occur for non-rigdj .4ccm files (rigdj adds a second load of the anthems automatically if no victory anthem is provided)
         if "victory" not in tmusic:
            messagebox.showwarning("Warning","No victory anthem information in {}; victory anthem will need to be played manually.".format(f))
         if tname is None:
            messagebox.showwarning("Warning","No team name found in {}. Opponent-specific music may not function properly.".format(f))
         if home:
            self.game.home_name = tname
            if self.home is not None:
               self.home.grid_forget()
               self.home.clear()
            self.home = TeamMenu(self, tname, tmusic, True, self.game)
            if self.away is not None:
               self.home.anthemButtons.awayButtonHook = self.away.anthemButtons
            self.home.grid(row = 1, column = 0, rowspan=2, sticky=N)
            if self.chants is not None:
               if "chant" in tmusic and tmusic["chant"] is not None:
                  print("Got {} chants for team /{}/.".format(len(tmusic["chant"]), tname))
                  for clist in tmusic["chant"]:
                     print("\t{}".format(clist.songname))
                  self.chants.setHome(parsed=tmusic["chant"])
               else:
                  print("No chants for team /{}/.".format(tname))
                  self.chants.setHome(parsed=None)
            if self.events is not None:
               self.events.setHome(parsed=events)
               print("Prepared events for team /{}/.".format(tname))
         else:
            self.game.away_name = tname
            if self.away is not None:
               self.away.grid_forget()
               self.away.clear()
            self.away = TeamMenu(self, tname, tmusic, False, self.game)
            if self.home is not None:
               self.home.anthemButtons.awayButtonHook = self.away.anthemButtons
            self.away.grid(row = 1, column = 2, rowspan=2, sticky=N)
            if self.chants is not None:
               if "chant" in tmusic and tmusic["chant"] is not None:
                  print("Got {} chants for team /{}/.".format(len(tmusic["chant"]), tname))
                  for clist in tmusic["chant"]:
                     print("\t{}".format(clist.songname))
                  self.chants.setAway(parsed=tmusic["chant"])
               else:
                  print("No chants for team /{}/.".format(tname))
                  self.chants.setAway(parsed=None)
            if self.events is not None:
               self.events.setAway(parsed=events)
               print("Prepared events for team /{}/.".format(tname))
         self.scoreWidget.updateLabels()
         self.game.clear()
         self.scoreWidget.updateScore()
      else:
         messagebox.showerror("Error","File {} not found.".format(f))

   def activateSENPAI (self):
      self.SENPAI = ThreadSENPAI()
      self.chants.start(self.SENPAI)
      self.events.start(self.SENPAI)
      try:
         self.SENPAI.start()
         print("SENPAI connection established.")
      except Exception as e:
         messagebox.showerror("Unable to start SENPAI!",str(e))


def resource_path(relative_path):
   """ Get absolute path to resource, works for dev and for PyInstaller """
   try:
      # PyInstaller creates a temp folder and stores path in _MEIPASS
      base_path = sys._MEIPASS
   except Exception:
      base_path = abspath(".")
   return join(base_path, relative_path)

def main ():
   master = Tk()
   try:
      datafile = resource_path("rigdio.ico")
      master.iconbitmap(default=datafile)
   except:
      pass
   master.title("rigdio {}".format(version))

   rigdio = Rigdio(master)
   rigdio.pack()
   try:
      mainloop()
   except KeyboardInterrupt:
      return

if __name__ == '__main__':
   if len(sys.argv) > 1 and sys.argv[1] == "gencfg":
      print("Generating config file rigdio.yml")
      genCfg()
   else:
      main()