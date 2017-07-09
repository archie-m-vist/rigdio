from tkinter import *
import tkinter.filedialog as filedialog
import tkinter.messagebox as messagebox
from tkinter.simpledialog import Dialog
import tkinter.font
from condition import *
from conditioneditor import ConditionDialog
from rigparse import parse
from rigdj_util import *
from version import rigdj_version as version

from logger import startLog
if __name__ == '__main__':
   startLog("rigdj.log")
   print("rigDJ {}".format(version))

# row usage
#  0 - load/save/save as
#  1 - team name
#  2 - player information
#  3 - headings
# 3+ - songs and conditions

class SongRow:
   def __init__ (self, editor, clist):
      self.editor = editor
      self.master = self.editor.teamMenu
      self.clist = clist
      self.songName = StringVar()
      self.songNameEntry = Entry(self.master, textvariable = self.songName)
      self.songNameEntry.insert(0,self.clist.songname)
      self.songNameButton = Button(self.master, text="Open File", command=self.findSong)
      self.newConditionButton = Button(self.master, text="New Condition", command=self.newCondition)
      self.conditionButtons = []
      for index in range(len(self.clist)):
         button = Button(self.master, text=str(self.clist[index]), command=lambda: self.editCondition(index))
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
      self.clist.songname = self.songName.get()

   def findSong (self):
      songname = filedialog.askopenfilename(filetypes = (("Audio Files","*.mp3 *.wav *.ogg *.flac"), ("All Files", "*")))
      self.songNameEntry.clear(0,END)
      self.songNameEntry.insert(0,songname)

   def newCondition (self):
      self.editCondition(len(self.clist))

   def editCondition (self, index):
      # check if condition is new
      if index == len(self.clist):
         condition = None
      # check if index is out of range
      elif (index < 0 or index > len(self.clist) ):
         raise KeyError("editCondition index must be <= length of condition list.")
      else:
         condition = self.clist[index]
      # edit condition in its own window
      result = ConditionDialog(self.master,condition,index == len(self.clist)).condition
      if result is not None:
         if result == -1:
            self.clist.pop(index)
         else:
            if index == len(self.clist):
               self.clist.append(result)
            else:
               self.clist[index] = result
         self.editor.updateSongMenu(uiName(self.clist.pname))

class Editor:
   def __init__ (self, master):
      # tkinter master window
      self.master = master
      # save/load
      self.menuButtons = self.buildFileMenu()
      self.menuButtons.pack()
      # file name of the .4ccm
      self.filename = None
      # team editor portion
      self.teamMenu = self.buildTeamEditor()
      self.teamMenu.pack()

      self.updatePlayerMenu()

   def buildFileMenu (self):
      """
         Constructs the file save/load menu buttons and returns a tk frame containing them.
      """
      buttons = Frame(self.master)
      self.loadButton = Button(buttons, text="Load .4ccm", command=self.load4ccm)
      self.loadButton.pack(side=LEFT)
      self.saveButton = Button(buttons, text="Save .4ccm", command=self.save4ccm)
      self.saveButton.pack(side=LEFT)
      self.saveAsButton = Button(buttons, text="Save .4ccm As...", command=self.save4ccmas)
      self.saveAsButton.pack(side=LEFT)
      return buttons

   def buildTeamEditor(self):
      """
         Constructs the team editing menu and returns a tk frame containing it.
      """
      frame = Frame(self.master)
      # team name
      Label(frame, text="Team:", font="-weight bold").grid(row=1,column=0,sticky=W)
      self.teamEntry = Entry(frame)
      self.teamEntry.grid(row=1,column=1)
      # dict mapping players to lists of ConditionList objects
      self.players = {"Anthem" : [], "Goalhorn" : [], "Victory Anthem" : []}
      plist = list(self.players.keys())
      plist.sort()
      # player dropdown menu
      ## label
      Label(frame, text="Player:", font="-weight bold").grid(row=2,column = 0,sticky=W)
      ## player variable
      self.player = StringVar()
      self.player.set("Anthem")
      ## actual optionmenu
      self.playerMenu = OptionMenu(frame, self.player, *plist, command=self.updateSongMenu)
      setMaxWidth(plist,self.playerMenu)
      self.playerMenu.grid(row = 2, column = 1)
      ## adding new players
      self.playerEntry = Entry(frame)
      self.playerEntry.grid(row = 2,column = 2)
      self.playerButton = Button(frame, text="Add Player", command=self.newplayer)
      self.playerButton.grid(row = 2, column = 3)
      # song listing menu
      self.songMenu = []
      ## headings
      Label(frame, text="Song Location").grid(row=3,column=0,columnspan=2)
      Label(frame, text="Conditions").grid(row=3,column=2,columnspan=2)
      ## new song buton
      self.newSongButton = Button(frame, text="New Song", command=self.newSong)
      return frame

   def load4ccm (self):
      self.filename = filedialog.askopenfilename(filetypes = (("Rigdio export files", "*.4ccm"),("All files","*")))
      self.players, teamName = parse(self.filename,False)
      uiConvert(self.players)

      self.teamEntry.delete(0,END)
      self.teamEntry.insert(0,teamName)
      self.player.set("Anthem")
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
      plist.sort()
      self.playerMenu = OptionMenu(self.teamMenu, self.player,*plist, command=self.updateSongMenu)
      setMaxWidth(plist,self.playerMenu)
      self.playerMenu.grid(row = 2, column = 1)
      self.updateSongMenu("Anthem")

   def newSong (self):
      name = self.player.get()
      self.players[name].append(ConditionList(name, self.teamEntry.get(), [], "New Song"))
      self.updateSongMenu(name)

   def updateSongMenu (self, name):
      for row in self.songMenu:
         row.clear()
      self.newSongButton.grid_forget()
      self.songMenu = []
      print("Displaying songs for player {}.".format(name))
      clists = self.players[name]
      row = 4
      for clist in clists:
         conditionRow = SongRow(self,clist)
         conditionRow.draw(row)
         self.songMenu.append(conditionRow)
         row += 1
      self.newSongButton.grid(row = row, column = 0)

   def moveSongUp (self, index):
      name = self.player.get()
      self.players[name]

   def writefile (self,filename):
      if self.teamEntry.get() == "":
         messagebox.showwarning("Error","Team name cannot be empty.")
         return None
      outConvert(self.players)
      with open(filename, 'w') as outfile:
         print("name;{}".format(self.teamEntry.get()), file=outfile)
         # if no victory anthems provided, copy normal anthem
         if "victory" not in self.players or len(self.players["victory"]) == 0:
            self.players["victory"] = self.players["anthem"]
         for key in self.players.keys():
            if len(self.players[key]) > 0:
               print("Writing songs for key {}".format(key))
               for conditions in self.players[key]:
                  print("{};{}".format(key,conditions), file=outfile)
      uiConvert(self.players)

   def newplayer (self):
      name = self.playerEntry.get()
      if name in self.players:
         messagebox.showwarning("Error","Player {} already exists.".format(name))
         return
      else:
         self.players[name] = []
         print("Adding player {}.".format(name))
         self.updatePlayerMenu()


def main ():
   # tkinter master window
   master = Tk()
   master.title("rigDJ {}".format(version))
   # construct editor object in window
   dj = Editor(master)
   # run
   mainloop()

if __name__ == '__main__':
   main()