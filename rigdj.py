from tkinter import *
import tkinter.filedialog as filedialog
import tkinter.messagebox as messagebox
from tkinter.simpledialog import Dialog
import tkinter.font
from condition import *
from rigparse import parse

from logger import Logger
from rigdj_util import *

# row usage
#  0 - load/save/save as
#  1 - team name
#  2 - player information
#  3 - headings
# 3+ - songs and conditions

class ConditionEditor (Dialog):
   def conditions ():
      output = {
         "goals" : GoalCondition,
         "comeback" : ComebackCondition,
         "first" : FirstCondition,
         "opponent" : OpponentCondition,
         "not" : NotCondition,
         "start" : StartInstruction
      }
      return output

   def defaultTokens ():
      output = {
         "goals" : ["==",2],
         "comeback" : [],
         "first" : [],
         "opponent" : [""],
         "not" : [],
         "start" : ["0:00"]  
      }
      return output

   def __init__ (self, master, index, clist):
      self.pname = clist.pname
      self.tname = clist.tname
      self.index = index
      self.condition = None
      self.tokens = []
      self.fields = []
      self.elements = []
      self.master = master
      if index < len(clist):
         self.condition = clist[self.index]
         self.tokens = self.condition.tokens()
      Dialog.__init__(self,master,"Editing Condition")

   def body (self, master):
      Label(master, text="Condition Type").grid(row=0,column=0)
      self.master = master
      self.conditionType = StringVar()
      self.conditionType.set("")
      conditions = list(ConditionEditor.conditions().keys())
      conditions.sort()
      self.conditionTypeMenu = OptionMenu(master, self.conditionType, *list(ConditionEditor.conditions().keys()), command=self.changeConditionType)
      setMaxWidth(conditions,self.conditionTypeMenu)
      self.conditionTypeMenu.grid(row=0,column=1)
      if self.condition is not None:
         self.conditionType.set(self.condition.type())
         self.changeConditionType(self.condition.type(),False)

   def apply (self):
      self.tokens = [str(x.get()) for x in self.fields]
      self.condition = ConditionEditor.conditions()[self.conditionType.get()](self.pname, self.tname, self.tokens)

   def changeConditionType (self, value, refreshTokens = True):
      if value is "":
         return None
      # reset existing elements and fields if any
      self.fields = []
      for element in self.elements:
         element.grid_forget()
      self.elements = []
      # refresh tokens to default if refreshing tokens
      if refreshTokens:
         self.tokens = ConditionEditor.defaultTokens()[value]
      if value == "goals":
         self.elements.append(Label(self.master, text="Goals By Player"))
         self.elements[0].grid(row=1,column=0)
         # operator
         self.fields.append(StringVar())
         self.fields[0].set(self.tokens[0])
         operators = ["==", "!=", "<", ">", "<=", ">="]
         opSelector = OptionMenu(self.master, self.fields[0], *operators)
         setMaxWidth(operators, opSelector)
         opSelector.grid(row=1,column=1)
         self.elements.append(opSelector)
         # value
         self.fields.append(IntVar())
         self.fields[1].set(int(self.tokens[1]))
         countEntry = Entry(self.master, textvariable=self.fields[1])
         countEntry.grid(row=1,column=2)
         self.elements.append(countEntry)
      elif value == "comeback":
         pass
      elif value == "first":
         pass
      elif value == "opponent":
         pass
      elif value == "not":
         pass
      elif value == "start":
         pass

class SongRow:
   def __init__ (self, editor, clist):
      self.editor = editor
      self.master = self.editor.master
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
      print("new condition!")

   def editCondition (self, index):
      if (index < 0 or index >= len(self.clist) ):
         raise ValueError("Somehow editing nonexistent condition.")
      result = ConditionEditor(self.master,index,self.clist).condition
      try:
         if result is not None:
            self.clist[index] = result
            print(self.clist)
            self.editor.updateSongMenu(self.clist.pname)
      except Exception as e:
         print("error saving result:",e)


class Editor:
   def __init__ (self, master):
      # tkinter master window
      self.master = master
      # save/load
      self.loadButton = Button(self.master, text="Load .4ccm", command=self.load4ccm)
      self.loadButton.grid(row = 0, column = 0,sticky=E+W)
      self.saveButton = Button(self.master, text="Save .4ccm", command=self.save4ccm)
      self.saveButton.grid(row = 0, column = 1,sticky=E+W)
      self.saveAsButton = Button(self.master, text="Save .4ccm As...", command=self.save4ccmas)
      self.saveAsButton.grid(row = 0, column = 2,sticky=E+W)
      # file name of the .4ccm
      self.filename = None
      # team name
      Label(self.master, text="Team:", font="-weight bold").grid(row=1,column=0,sticky=W)
      self.teamEntry = Entry(self.master)
      self.teamEntry.grid(row=1,column=1)
      # dict mapping players to lists of ConditionList objects
      self.players = {"Anthem" : [], "Goalhorn" : [], "Victory Anthem" : []}
      plist = list(self.players.keys())
      plist.sort()
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
      # song listing menu
      self.songMenu = []
      ## headings
      Label(self.master, text="Song Location").grid(row=3,column=0,columnspan=2)
      Label(self.master, text="Conditions").grid(row=3,column=2,columnspan=2)
      ## new song buton
      self.newSongButton = Button(self.master, text="New Song", command=self.newSong)

      self.updatePlayerMenu()

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
      plist.sort()
      self.playerMenu = OptionMenu(self.master, self.player,*plist, command=self.updateSongMenu)
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
         self.updatePlayerMenu()


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