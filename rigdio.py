import sys
from os.path import isfile

from tkinter import *
import tkinter.filedialog as filedialog
import tkinter.messagebox as messagebox

from rigparse import parse
from gamestate import GameState
from songgui import *

import logger

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
      self.game = GameState()
      self.home = None
      self.away = None
      # file menu
      Button(self, text="Load Home Team", command=self.loadFile).grid(row=0, column=0)
      Button(self, text="Load Away Team", command=lambda: self.loadFile(False)).grid(row=0, column=2)
      # score widget
      self.scoreWidget = ScoreWidget(self, self.game)
      self.game.widget = self.scoreWidget
      self.scoreWidget.grid(row=0, column=1)

   def loadFile (self, home = True):
      f = filedialog.askopenfilename(filetypes = (("Rigdio export files", "*.4ccm"),("All files","*.*")))
      if isfile(f):
         print("Loading music instructions from {}.".format(f))
         tmusic, tname = parse(f)
         # copy anthem to victory anthem if none given
         if "victory" not in tmusic:
            messagebox.showwarning("Warning","No victory anthem information in {}; victory anthem will need to be played manually.".format(f))
         if tname is None:
            messagebox.showwarning("Warning","No team name found in {}. Opponent-specific music may not function properly.".format(f))
         if home:
            self.game.home_name = tname
            if self.home is not None:
               self.home.grid_forget()
            self.home = TeamMenu(self, tname, tmusic, True, self.game)
            self.home.grid(row = 1, column = 0, rowspan=2, sticky=N)
            self.scoreWidget.updateLabels()
            self.game.clear()
         else:
            self.game.away_name = tname
            if self.away is not None:
               self.away.grid_forget()
            self.away = TeamMenu(self, tname, tmusic, False, self.game)
            self.away.grid(row = 1, column = 2, rowspan=2, sticky=N)
            self.scoreWidget.updateLabels()
            self.game.clear()
      else:
         messagebox.showerror("Error","File {} not found.".format(f))

def main ():
   master = Tk()
   rigdio = Rigdio(master)
   rigdio.pack()
   try:
      mainloop()
   except KeyboardInterrupt:
      return

if __name__ == '__main__':
   main()