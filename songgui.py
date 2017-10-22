from tkinter import *
import tkinter.messagebox as messagebox
from rigparse import reserved
from rigdio_except import UnloadSong, SongNotFound
from condition import PlayerManager
from config import settings

class PlayerButtons:
   def __init__ (self, frame, clists, home, game, text = None):
      # song information
      self.clists = PlayerManager(clists,home,game)
      self.game = game
      # derived information
      self.song = None
      self.pname = clists[0].pname
      # text and buttons
      self.text = text
      # check if text is none (most players)
      if self.text is None:
         self.text = "\n".join([x.lstrip() for x in self.pname.split(",")])
         self.reserved = False
      # text was specified, so this is a button for a reserved keyword
      else:
         self.reserved = True
      self.listButton = Button(frame, text="?", command=self.showSongs, bg=settings.colours["home" if home else "away"])
      self.playButton = Button(frame, text=self.text, command=self.playSong, bg=settings.colours["home" if home else "away"])
      self.volume = Scale(frame, from_=0, to=100, orient=HORIZONTAL, command=self.clists.adjustVolume, showvalue=0)
      self.volume.set(100)

   def playSong (self):
      if self.clists.song is None:
         # score points if it's a goalhorn
         if self.pname not in reserved or self.pname == "goal":
            self.game.score(self.pname, self.clists.home)
         # pass it up to the list manager
         try:
            self.clists.playSong()
         # no song found
         except SongNotFound as e:
            print(e)
            messagebox.showwarning(e)
            return
         # set the button as sunken
         self.playButton.configure(relief=SUNKEN)
      else:
         # pause the song
         self.clists.pauseSong()
         # set the button as raised
         self.playButton.configure(relief=RAISED)

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

   def insert (self, row):
      self.listButton.grid(row=row,column=0,sticky=N+S, padx=2, pady=(5,0))
      self.playButton.grid(row=row,column=1,sticky=E+W, padx=2, pady=(5,0))
      self.volume.grid(row=row+1,column=0,columnspan=2,sticky=E+W, pady=(0,5))

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
      startRow = self.buildVictoryAnthemMenu() + 2
      # buttons for goalhorns
      self.buildGoalhornMenu(startRow)

   def buildAnthemButtons (self):
      PlayerButtons(self, self.players["anthem"], self.home, self.game, "Anthem").insert(0)

   def buildVictoryAnthemMenu (self):
      if "victory" in self.players:
         PlayerButtons(self, self.players["victory"], self.home, self.game, "Victory Anthem").insert(2)
         return 2
      else:
         return 0

   def buildGoalhornMenu (self, startRow):
      Label(self, text="Goalhorns").grid(row=startRow, column=0, columnspan=2)
      PlayerButtons(self, self.players["goal"], self.home, self.game, "Standard Goalhorn").insert(startRow+1)
      for i in range(len(self.playerNames)):
         name = self.playerNames[i]
         PlayerButtons(self, self.players[name], self.home, self.game).insert(startRow+2*i+3)

   def clear (self):
      for player in self.players.keys():
         for clist in self.players[player]:
            clist.disable()