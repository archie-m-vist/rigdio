from tkinter import *
import tkinter.filedialog as filedialog
import tkinter.messagebox as messagebox
import tkinter.font
from rigparse import parse

from logger import Logger
from rigdj_util import *

# row usage
#  0 - load/save/save as
#  1 - team name
#  2 - player information
#  3 - headings
# 3+ - songs and conditions

class SongRow:
   def __init__ (self, master, clist):
      self.master = master
      self.songName = StringVar()
      self.songNameEntry = Entry(self.master, textvariable = self.songName)
      self.songNameEntry.insert(0,clist.songname)
      self.songNameButton = Button(self.master, text="Open File", command=self.findSong)
      self.newConditionButton = Button(self.master, text="New Condition", command=self.newCondition)
      self.conditionButtons = []
      print(clist, len(clist))
      for condition in clist:
         button = Button(self.master, text=str(condition), command=lambda: print(condition))
         self.conditionButtons.append(button)

   def draw (self, row):
      self.songNameButton.grid(row = row, column = 0)
      self.songNameEntry.grid(row = row, column = 1)
      self.newConditionButton.grid(row = row, column = 2)
      for i in range(len(self.conditionButtons)):
         button = self.conditionButtons[i]
         button.grid(row = row, column = 3+i)

   def clear (self):
      self.songNameEntry.grid_forget()
      self.songNameButton.grid_forget()
      self.newConditionButton.grid_forget()
      for button in self.conditionButtons:
         button.grid_forget()

   def findSong (self):
      songname = filedialog.askopenfilename(filetypes = (("Audio Files","*.mp3 *.wav *.ogg *.flac"), ("All Files", "*")))
      self.songNameEntry.clear(0,END)
      self.songNameEntry.insert(0,songname)

   def newCondition (self):
      print("new condition!")

class Editor:
   def __init__ (self, master):
      # tkinter master window
      self.master = master
      # file name of the .4ccm
      self.filename = None
      # team name
      Label(self.master, text="Team:", font="-weight bold").grid(row=1,column=0,sticky=W)
      self.teamEntry = Entry(self.master)
      self.teamEntry.grid(row=1,column=1)
      # dict mapping players to lists of ConditionList objects
      self.players = {"Anthem" : [], "Goalhorn" : [], "Victory Anthem" : []}
      plist = list(self.players.keys())
      # player dropdown menu
      ## label
      Label(self.master, text="Player:", font="-weight bold").grid(row=2,column = 0,sticky=W)
      ## player variable
      self.player = StringVar(self.master)
      self.player.set("Anthem")
      ## actual optionmenu
      self.playerMenu = OptionMenu(self.master, self.player, *plist, command=self.updateSongMenu)
      setMaxWidth(plist,self.playerMenu)
      self.playerMenu.grid(row = 2, column = 1)
      ## adding new players
      self.playerEntry = Entry(self.master)
      self.playerEntry.grid(row = 2,column = 2)
      self.playerButton = Button(self.master, text="Add Player", command=self.newplayer)
      self.playerButton.grid(row = 2, column = 3)
      # save/load
      self.loadButton = Button(self.master, text="Load .4ccm", command=self.load4ccm)
      self.loadButton.grid(row = 0, column = 0)
      self.saveButton = Button(self.master, text="Save .4ccm", command=self.save4ccm)
      self.saveButton.grid(row = 0, column = 1)
      self.saveAsButton = Button(self.master, text="Save .4ccm As...", command=self.save4ccmas)
      self.saveAsButton.grid(row = 0, column = 2)
      # song listing menu
      self.songMenu = []
      ## headings
      Label(self.master, text="Song Location").grid(row=3,column=0,columnspan=2)
      Label(self.master, text="Conditions").grid(row=3,column=2,columnspan=2)
      ## new song buton
      self.newSongButton = Button(self.master, text="New Song", command=self.newSong)

   def load4ccm (self):
      self.filename = filedialog.askopenfilename(filetypes = (("Rigdio export files", "*.4ccm"),("All files","*")))
      self.players, teamName = parse(self.filename,False)
      uiConvert(self.players)

      self.teamEntry.delete(0,END)
      self.teamEntry.insert(0,teamName)
      self.updatePlayerMenu()

   def save4ccm (self):
      if self.filename is None:
         self.filename = filedialog.asksaveasfilename(filetypes = (("Rigdio export files", "*.4ccm"),("All files","*")))
      self.writefile(self.filename)

   def save4ccmas (self):
      self.filename = filedialog.asksaveasfilename(filetypes = (("Rigdio export files", "*.4ccm"),("All files","*")))
      self.writefile(self.filename)

   def updatePlayerMenu (self):
      # add player menu and "add player" button if not already present
      if self.playerMenu is not None:
         self.playerMenu.grid_forget()
      plist = list(self.players.keys())
      self.playerMenu = OptionMenu(self.master, self.player,*plist, command=self.updateSongMenu)
      setMaxWidth(plist,self.playerMenu)
      self.playerMenu.grid(row = 2, column = 1)
      self.updateSongMenu("Anthem")

   def newSong (self):
      name = self.player.get()
      self.players[name].append(ConditionList(name, self.teamEntry.get(), [], "New Song"))
      updateSongMenu()

   def updateSongMenu (self, name):
      for row in self.songMenu:
         row.clear()
      self.songMenu = []
      print("Displaying songs for player {}.".format(name))
      clists = self.players[name]
      row = 4
      for clist in clists:
         conditionRow = SongRow(self.master,clist)
         conditionRow.draw(row)
         self.songMenu.append(conditionRow)
         row += 1

   def writefile (self,filename):
      with open(filename, 'w') as outfile:
         print("name;{}".format(self.teamEntry.get()), file=outfile)
         outConvert(self.players)
         for key in self.players.keys():
            if len(self.players[key]) > 0:
               print("Writing songs for key {}".format(key))
               for conditions in self.players[key]:
                  print("{};{}".format(key,conditions), file=outfile)

   def newplayer (self):
      name = self.playerEntry.get()
      if name in self.players:
         messagebox.showinfo("Error","Player {} already exists.".format(name))
         return
      else:
         self.players[name] = []
         updatePlayerMenu()


def main ():
   # set up logging
   sys.stdout = Logger("rigdj.log")
   sys.stderr = sys.stdout
   # tkinter master window
   master = Tk()
   master.minsize(640,480)
   # construct editor object in window
   dj = Editor(master)
   # run
   mainloop()

if __name__ == '__main__':
   main()