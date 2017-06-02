from tkinter import *
import tkinter.messagebox as messagebox
from rigparse import reserved

class PlayerButtons (Frame):
   def __init__ (self, master, clists, home, game, text = None):
      Frame.__init__(self, master)
      # song information
      self.clists = clists
      self.home = home
      self.game = game
      self.text = text
      # derived information
      self.song = None
      self.pname = clists[0].pname
      # text and buttons
      ## check if text is none (i.e., it's a reserved keyword with an overridden name)
      if self.text is None:
         self.text = self.pname
         self.reserved = False
      else:
         self.reserved = True
      Button(self, text="?", command=self.showSongs).grid(row = 0, column = 0)
      self.playButton = Button(self, text=self.text, command=self.playSong)
      self.playButton.grid(row = 0, column = 1)

   def playSong (self):
      if self.song is None:
         # score points if it's a goalhorn
         if self.pname not in reserved or self.pname == "goal":
            self.game.score(self.pname, self.home)
         for clist in self.clists:
            if clist.check(self.game):
               self.song = clist
               print("Playing",self.song.songname)
               self.song.play()
               self.playButton.configure(relief=SUNKEN)
               return
         messagebox.showwarning("No Song Found", "No song for player {} matches current game sstate; no music will play.".format(self.pname))
      else:
         self.song.pause()
         self.playButton.configure(relief=RAISED)
         self.song = None

   def showSongs (self):
      text = self.text
      if not self.reserved:
         text = "Player {}".format(self.text)
      title = "Listing Songs for {}".format(text)
      text = ""
      for clist in self.clists:
         if len(text) == 0:
            text = str(clist)
         else:
            text = "\n".join([text, str(clist)])
      messagebox.showinfo(title, text)

class TeamMenu (Frame):
   def __init__ (self, master, tname, players, home, game):
      Frame.__init__(self, master)
      # store information from constructor
      self.tname = tname
      self.players = players
      self.home = home
      self.game = game
      # list of player names for use in buttons
      self.playerNames = [x for x in self.players.keys() if x not in reserved]
      self.playerNames.sort()
      # tkinter frame containing menu
      # button for anthem
      self.buildAnthemButtons()
      # buttons for victory anthems
      self.buildVictoryAnthemMenu()
      # buttons for goalhorns
      self.buildGoalhornMenu()

   def buildAnthemButtons (self):
      PlayerButtons(self, self.players["anthem"], self.home, self.game, "Anthem").pack()

   def buildVictoryAnthemMenu (self):
      if "victory" in self.players:
         PlayerButtons(self, self.players["victory"], self.home, self.game, "Victory Anthem").pack()

   def buildGoalhornMenu (self):
      Label(self, text="Goalhorns").pack()
      goalFrame = Frame(self)
      PlayerButtons(goalFrame, self.players["goal"], self.home, self.game, "Standard Goalhorn").pack()
      for name in self.playerNames:
         PlayerButtons(goalFrame, self.players[name], self.home, self.game).pack()
      goalFrame.pack()