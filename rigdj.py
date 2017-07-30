from version import rigdj_version as version
from logger import startLog
if __name__ == '__main__':
   startLog("rigdj.log")
   print("rigDJ {}".format(version))

from tkinter import *
import tkinter.filedialog as filedialog
import tkinter.messagebox as messagebox
from tkinter.simpledialog import Dialog
import tkinter.font

from condition import *
from conditioneditor import ConditionDialog

from rigdj_util import *
from rigparse import parse, reserved

specialNames = set(["Goalhorn", "Anthem", "Victory Anthem"])

class ConditionButton (Button):
   def __init__ (self, songrow, index, **kwargs):
      """
         Constructs a ConditionButton.

         master must be a SongRow object.
      """
      if "command" in kwargs or "text" in kwargs:
         raise ValueError("Cannot specify command or text for ConditionButton.")

      self.cond = songrow[index] if index < len(songrow) else None
      self.index = index
      self.songrow = songrow

      txt = str(self.cond) if self.cond is not None else "Add Condition"
      super().__init__(self.songrow.master, command=self.edit, text=txt, **kwargs)

   def edit (self):
      temp = ConditionDialog(self.master,self.cond,self.cond==None).condition
      if temp is not None:
         if temp == -1:
            # delete condition
            self.songrow.pop(self.index)
         else:
            if self.index < len(self.songrow):
               self.songrow[self.index] = temp
            else:
               self.songrow.append(temp)
            self.cond = temp
         self.songrow.update()

class SongRow:
   def __init__ (self, songed, row, clist):
      self.master = songed
      self.clist = clist
      self.row = row
      self.strRow = StringVar()
      self.baseElements = self.buildBaseElements()
      self.conditionButtons = []
      self.elements = self.baseElements
      # initialise filename
      self.songNameEntry.insert(0,clist.songname)
      self.songNameEntry.xview_moveto(1)

   def buildBaseElements (self):
      output = []
      output.append(Button(self.master,text="▼", command=lambda: self.master.moveSongDown(self.row-1)))
      output.append(Label(self.master,textvariable=self.strRow))
      output.append(Button(self.master,text="▲", command=lambda: self.master.moveSongUp(self.row-1)))
      output.append(Label(self.master,text=" "))
      output.append(Button(self.master,text="Open"))
      self.songNameEntry = Entry(self.master, width=50)
      output.append(self.songNameEntry)
      output.append(Label(self.master,text=" "))
      return output

   def clear (self):
      for element in self.elements:
         element.grid_forget()

   def update (self):
      self.strRow.set(str(self.row))
      self.clist.songname = self.songNameEntry.get()
      for element in self.elements:
         element['state'] = 'normal'
         element.grid_forget()
      
      # disable arrows if the row is inappropriate
      if self.row == 1:
         self.baseElements[2]['state'] = 'disabled'
      if self.row == self.master.count():
         self.baseElements[0]['state'] = 'disabled'

      # construct condition buttons
      self.conditionButtons = [ConditionButton(self,index) for index in range(len(self.clist))]
      self.conditionButtons.append(ConditionButton(self,len(self)))
      # construct complete list of elements
      self.elements = self.baseElements + self.conditionButtons
      # draw elements
      for index in range(len(self.elements)):
         self.elements[index].grid(row=self.row,column=index,sticky=N+E+W+S,padx=2,pady=1)

   def pop (self, index=0):
      temp = self.clist.pop(index)
      self.update()
      return temp

   def append (self, element):
      self.clist.append(element)
      self.update()

   def __getitem__ (self, index):
      return self.clist[index]

   def __setitem__ (self, index, value):
      self.clist[index] = value

   def __len__ (self):
      return len(self.clist)

class SongEditor (Frame):
   def __init__ (self, master, clists = []):
      super().__init__(master)
      self.songrows = []
      self.newSongButton = Button(self,text="Add Song",command=self.addSong)
      self.load(clists)

   def load (self, clists):
      # clear previous information
      for child in self.winfo_children():
         child.grid_forget()
      # reconstruct
      self.songrows = []
      # turn clists into song rows
      for index in range(len(clists)):
         self.songrows.append(SongRow(self,index+1,clists[index]))
      self.update(True)

   def addSong (self):
      self.songrows.append(SongRow(self,len(self.songrows)+1,ConditionList()))
      self.update(len(self.songrows)==1)

   def update (self, headings = False):
      for index in range(len(self.songrows)):
         songrow = self.songrows[index]
         songrow.row = index+1
         songrow.update()
      if len(self.songrows) > 0 and headings:
         Label(self,text="Priority").grid(row=0,column=0,columnspan=3,sticky=E+W)
         Label(self,text="Song Location").grid(row=0,column=4,columnspan=2,sticky=E+W)
         Label(self,text="Conditions").grid(row=0,column=7,columnspan=999,sticky=W)
      self.newSongButton.grid_forget()
      self.newSongButton.grid(row=len(self.songrows)+1,column=0,columnspan=3,sticky=E+W, padx=2, pady=2)

   def moveSongUp (self, index):
      temp = self.songrows.pop(index)
      self.songrows.insert(index-1,temp)
      self.update()

   def moveSongDown (self, index):
      temp = self.songrows.pop(index)
      self.songrows.insert(index+1,temp)
      self.update()

   def clists (self):
      self.update()
      return [row.clist for row in self.songrows]

   def count (self):
      return len(self.songrows)

class PlayerSelectFrame (Frame):
   def __init__ (self, master, command = None, players = []):
      super().__init__(master)
      Button(self, text="Add Player", command=self.addPlayer).grid(row=0,column=0,sticky=E+W,padx=5,pady=5)
      self.newPlayerEntry = Entry(self, width=30)
      self.newPlayerEntry.grid(row=0,column=1, sticky=W,padx=5,pady=5)
      # songs for each player
      self.songs = {
         "Anthem" : [],
         "Victory Anthem" : [],
         "Goalhorn" : []
      }
      # create list selector with default options
      self.playerMenu = ScrollingListbox(self)
      self.playerMenu.insert(END,"Anthem")
      self.playerMenu.insert(END,"Victory Anthem")
      self.playerMenu.insert(END,"Goalhorn")
      self.playerMenu.grid(row=1,column=0,padx=5,pady=5,sticky=N)
      self.current = None
      # create song editor
      self.songEditor = SongEditor(self)
      self.songEditor.grid(row=1,column=1,sticky=NE+SW,padx=5,pady=5)
      # add any players passed to constructor
      self.updateList(players)
      # bind callback to list
      self.bindSelect(self.loadSongEditor)
      self.playerMenu.selection_set(first = 0)
      self.loadSongEditor("Anthem")

   def loadSongEditor (self, pname):
      if self.current is not None:
         self.songs[self.current] = self.songEditor.clists()
      clists = self.songs[pname]
      self.songEditor.load(clists)
      self.current = pname

   def updateList (self, players = []):
      self.playerMenu.delete(3,END)
      self.songs = {
         "Anthem" : [],
         "Victory Anthem" : [],
         "Goalhorn" : []
      }
      players.sort()
      for player in players:
         self.playerMenu.insert(END,player)
      setMaxWidth(players+list(specialNames),self.playerMenu)

   def updateSongs (self, songs):
      for player in self:
         self.songs[player] = songs[player]
      self.current = None
      self.loadSongEditor("Anthem")

   def addPlayer (self):
      name = self.newPlayerEntry.get()
      if name == "":
         messagebox.showwarning("Error","Player name cannot be empty.")
         return
      i = 3
      while i < self.playerMenu.size() and name > self.playerMenu.get(i):
         i += 1
      if self.playerMenu.get(i) == name:
         messagebox.showwarning("Error","Player {} already exists.".format(name))
         return
      self.playerMenu.insert(i,name)
      self.songs[player] = []

   def get (self):
      index = self.playerMenu.curselection()[0]
      return self.playerMenu.get(index)

   def __getitem__ (self, index):
      if index < 0 or index >= self.playerMenu.size():
         raise IndexError
      return self.playerMenu.get(index)

   def bindSelect (self, command):
      def eventToName (event):
         index = int(event.widget.curselection()[0])
         return event.widget.get(index)
      self.playerMenu.bind('<<ListboxSelect>>',lambda event, copy=command: copy(eventToName(event)))

class Editor (Frame):
   def __init__ (self, master):
      # tkinter master window
      super().__init__(master)
      # save/load
      fileMenu = self.buildFileMenu()
      fileMenu.pack(anchor="nw")
      # file name of the .4ccm
      self.filename = None
      # team editor portion
      temp = Frame(self, pady=5)
      Label(temp, text="Team Name:").grid(row=0,column=0)
      self.teamEntry = Entry(temp, width=20)
      self.teamEntry.grid(row=0,column=1)
      temp.pack(anchor="nw")
      self.playerMenu = PlayerSelectFrame(self)
      self.playerMenu.pack(anchor="nw")

   def buildFileMenu (self):
      """
         Constructs the file save/load menu buttons.
      """
      buttons = Frame(self)
      self.loadButton = Button(buttons, text="Load .4ccm", command=self.load4ccm)
      self.loadButton.pack(side=LEFT)
      self.saveButton = Button(buttons, text="Save .4ccm", command=self.save4ccm)
      self.saveButton.pack(side=LEFT)
      self.saveAsButton = Button(buttons, text="Save .4ccm As...", command=self.save4ccmas)
      self.saveAsButton.pack(side=LEFT)
      return buttons

   def load4ccm (self):
      self.filename = filedialog.askopenfilename(filetypes = (("Rigdio export files", "*.4ccm"),("All files","*")))
      songs, teamName = parse(self.filename,False)
      uiConvert(songs)

      self.teamEntry.delete(0,END)
      self.teamEntry.insert(0,teamName)
      self.teamEntry.xview_moveto(1)
      normalPlayers = [x for x in songs if x not in specialNames]
      self.playerMenu.updateList(normalPlayers)
      self.playerMenu.updateSongs(songs)

   def save4ccm (self):
      if self.filename is None:
         self.filename = filedialog.asksaveasfilename(defaultextension=".4ccm", filetypes = (("Rigdio export files", "*.4ccm"),("All files","*")))
      self.writefile(self.filename)

   def save4ccmas (self):
      self.filename = filedialog.asksaveasfilename(defaultextension=".4ccm", filetypes = (("Rigdio export files", "*.4ccm"),("All files","*")))
      self.writefile(self.filename)

   def writefile (self,filename):
      if self.teamEntry.get() == "":
         messagebox.showerror("Error","Team name cannot be empty.")
         return None
      with open(filename, 'w') as outfile:
         players = self.playerMenu.songs
         flag = False
         outConvert(players)
         print("# team identifier", file=outfile)
         print("name;{}".format(self.teamEntry.get()), file=outfile)
         print("",file=outfile)
         # if no victory anthems provided, copy normal anthem
         print("# reserved names", file=outfile)
         if "victory" not in players or len(players["victory"]) == 0:
            players["victory"] = players["anthem"]
         for player in self.playerMenu:
            if player not in reserved and flag == False:
               print("",file=outfile)
               print("# regular players", file=outfile)
               flag = True
            if len(self.players[player]) > 0:
               print("Writing songs for player {}.".format(player))
               for conditions in players[player]:
                  print("{};{}".format(player,conditions), file=outfile)
            else:
               print("List for player {} is empty, will be ignored.").format(player)
         uiConvert(players)

def main ():
   # tkinter master window
   mainWindow = Tk()
   mainWindow.title("rigDJ {}".format(version))
   # construct editor object in window
   dj = Editor(mainWindow)
   dj.pack()
   # run
   mainloop()

if __name__ == '__main__':
   main()