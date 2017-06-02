from tkinter import *
import tkinter.filedialog as filedialog
import tkinter.messagebox as messagebox
from tkinter.simpledialog import Dialog
import tkinter.font
from condition import *
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

class ConditionEditor (Dialog):
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

   def __init__ (self, master, condition, new = False):
      self.condition = condition
      self.master = master
      self.pname = condition.pname
      self.tname = condition.tname
      self.tokens = []
      self.subConditions = []
      if str(self.condition) != "nullCond":
         self.tokens = self.condition.tokens()
         self.updateSubConditions()
      # UI information
      self.fields = []
      self.elements = []
      # check if new 
      self.new = new
      Dialog.__init__(self,master,"Editing Condition")

   def body (self, frame):
      self.bodyFrame = frame
      self.conditionType = StringVar()
      self.conditionType.set("")
      if str(self.condition) != "nullCond":
         self.conditionType.set(self.condition.type())
      # condition type selector
      conditionTypeMenu, self.conditionDescLabel = self.buildConditionTypeMenu()
      conditionTypeMenu.pack()
      
      self.mainEditor = Frame(frame)
      self.mainEditor.pack()
      self.changeConditionType(self.conditionType.get(),False)

   def buildConditionTypeMenu (self):
      """
         Builds the condition type selector and docstring menu.
      """
      frame = Frame(self.bodyFrame)
      selectorFrame = Frame(frame)
      Label(selectorFrame, text="Condition Type", font="-weight bold").pack(side=LEFT)
      ctypes = list(conditions.keys())
      ctypes.sort()
      selector = OptionMenu(selectorFrame, self.conditionType, *ctypes, command=self.changeConditionType)
      setMaxWidth(ctypes,selector)
      selector.pack(side=LEFT)
      selectorFrame.pack()
      # condition description
      descLabelFrame = Frame(frame)
      descLabel = Label(descLabelFrame, text="", anchor=W, justify=LEFT, wraplength="10c")
      descLabel.pack()
      Label(descLabelFrame, text="", width=60).pack()
      descLabelFrame.pack()
      return frame, descLabel

   def validate (self):
      ctype = self.conditionType.get()
      if ctype == "goals":
         try: 
            int(self.fields[1].get())
         except:
            messagebox.showwarning("Input Error", "Goals instruction must be compared to an integer.")
            return False
      elif ctype == "start":
         if timeToSeconds(self.fields[0].get()) is None:
            messagebox.showwarning("Input Error", "Start instruction requires a time formatted as any of: day:hour:min:sec, hour:min:sec, min:sec, or sec.")
            return False
      elif ctype == "not":
         if self.subConditions[0] == None:
            messagebox.showwarning("Input Error", "No condition defined for not condition.")
      return True

   def apply (self):
      self.tokens = [str(x.get()) for x in self.fields]
      ctype = self.conditionType.get()
      if ctype == "opponent":
         self.tokens = self.tokens[0].split(" ")
      
      if ctype == "not":
         self.condition = NotCondition(self.pname, self.tname, condition = self.subConditions[0])
      else:
         self.condition = conditions[ctype](self.pname, self.tname, self.tokens)

   def buttonbox(self):
        box = Frame(self)

        w = Button(box, text="OK", width=10, command=self.ok, default=ACTIVE)
        w.pack(side=LEFT, padx=5, pady=5)
        if not self.new:
           w = Button(box, text="Delete", width=10, command=self.delete)
           w.pack(side=LEFT, padx=5, pady=5)
        w = Button(box, text="Cancel", width=10, command=self.cancel)
        w.pack(side=LEFT, padx=5, pady=5)

        self.bind("<Return>", self.ok)
        self.bind("<Escape>", self.cancel)

        box.pack()

   def delete (self):
      self.condition = -1
      self.cancel()

   def changeConditionType (self, value, resetTokens = True):
      # reset existing elements and fields if any
      self.fields = []
      for element in self.elements:
         element.grid_forget()
      self.elements = []
      
      # update description label
      if value == "":
         desc = "No condition type selected."
      else:
         desc = conditions[value].desc
      self.conditionDescLabel['text'] = desc

      # if no type selected, we're done
      if value is "":
         return None

      # reset tokens to default if necessary
      if resetTokens:
         self.tokens = ConditionEditor.defaultTokens()[value]
         self.subConditions = []

      # construct body of each condition type
      if value == "goals":
         self.elements.append(Label(self.mainEditor, text="Goals By Player"))
         self.elements[-1].grid(row=2,column=0,sticky=W)
         # operator
         self.fields.append(StringVar())
         self.fields[0].set(self.tokens[0])
         operators = ["==", "!=", "<", ">", "<=", ">="]
         opSelector = OptionMenu(self.mainEditor, self.fields[0], *operators)
         setMaxWidth(operators, opSelector)
         opSelector.grid(row=2,column=1,sticky=W)
         self.elements.append(opSelector)
         # value
         self.fields.append(StringVar())
         self.fields[1].set(str(self.tokens[1]))
         countEntry = Entry(self.mainEditor, textvariable=self.fields[1])
         countEntry.grid(row=2,column=2,sticky=W)
         self.elements.append(countEntry)
      elif value == "comeback":
         # comeback takes no arguments
         pass
      elif value == "first":
         # first takes no arguments
         pass
      elif value == "opponent":
         self.elements.append(Label(self.mainEditor, text="Opponent is Any Of"))
         self.elements[-1].grid(row=2,column=0,sticky=W)
         self.fields.append(StringVar())
         opponentEntry = Entry(self.mainEditor, textvariable=self.fields[0])
         opponentEntry.grid(row=2,column=1,sticky=W+E)
         self.elements.append(opponentEntry)
      elif value == "not":
         self.elements.append(Label(self.mainEditor, text="Not"))
         self.elements[-1].grid(row=2,column=0,sticky=W)
         buttonText = "New Condition"
         if len(self.subConditions) > 0:
            buttonText = str(self.subConditions[0])
         else:
            self.subConditions.append(Condition(self.pname,self.tname))
         self.elements.append(Button(self.mainEditor, text=buttonText, command = lambda: self.editSubCondition(0)))
         self.elements[-1].grid(row=2,column=1)
         pass
      elif value == "start":
         self.elements.append(Label(self.mainEditor, text="Start Playback At"))
         self.elements[-1].grid(row=2,column=0,sticky=W)
         self.fields.append(StringVar())
         timeEntry = Entry(self.mainEditor, textvariable=self.fields[0])
         timeEntry.grid(row=2,column=1,sticky=W+E)
         self.elements.append(opponentEntry)

   def updateSubConditions (self):
      self.subConditions = []
      if self.condition.type() == "not":
         self.subConditions.append(self.condition.condition)

   def editSubCondition (self, index):
      condition = self.subConditions[index]
      try:
         self.subConditions[index] = ConditionEditor(self.master,condition,condition.type() == Condition.null).condition
      except Exception as e:
         print(e)
      self.changeConditionType(self.conditionType.get(), False)

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
         condition = Condition(self.clist.pname, self.clist.tname, True)
      # check if index is out of range
      elif (index < 0 or index > len(self.clist) ):
         raise KeyError("editCondition index must be <= length of condition list.")
      else:
         condition = self.clist[index]
      # edit condition in its own window
      result = ConditionEditor(self.master,condition,index == len(self.clist)).condition
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