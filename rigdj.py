import inspect

from version import rigdj_version as version
from logger import startLog
if __name__ == '__main__':
   startLog("rigdj.log")
   print("rigDJ {}".format(version))

from io import StringIO

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
   """
      Button object that opens the ConditionDialog editor.

      To be placed inside a SongRow.
   """
   def __init__ (self, songrow, index, **kwargs):
      """
         Constructs a ConditionButton.
      """
      # command and text are covered by the subclass, don't kwarg them
      if "command" in kwargs or "text" in kwargs:
         raise ValueError("Cannot specify command or text for ConditionButton.")

      # store condition, location in songrow, and the row object itself
      self.cond = songrow[index] if index < len(songrow) else None
      self.index = index
      self.songrow = songrow

      # every condition but the end one is the text on the button; if no condition, it's the new condition button
      txt = str(self.cond) if self.cond is not None else "Add Condition"
      # songrow.master is the SongEditor frame
      super().__init__(self.songrow.master, command=self.edit, text=txt, **kwargs)

   def edit (self):
      # get a condition from a ConditionDialog
      temp = ConditionDialog(self.master,self.cond,self.cond==None).condition
      # if None, was a NewCondition and Cancel was pressed
      if temp is not None:
         # if -1, existing condition asked for the delete
         if temp == -1:
            self.songrow.pop(self.index)
         # otherwise insert at the appropriate index
         else:
            if self.index < len(self.songrow):
               self.songrow[self.index] = temp
            else:
               self.songrow.append(temp)
            # store temp as this button's new condition, in case update fails for some reason
            self.cond = temp
         # we've added or changed a condition, so update row and trigger callbacks
         self.songrow.update(True)

class SongRow:
   def __init__ (self, songed, row, clist):
      # self.master is a SongEditor object; referenced for callbacks and drawing
      self.master = songed
      # condition list for this row
      self.clist = clist
      # row in which to draw this row; equal to its index in self.master's clists plus 1
      self.row = row
      # row number as a string variable, for swapping of rows
      self.strRow = StringVar()
      # baseElements is all non-ConditionButton objects, constant across all SongRow objects
      self.baseElements = self.buildBaseElements()
      # conditionButtons is the 
      self.conditionButtons = []
      # self.elements is a list of all elements in the row; it's baseElements + conditionButtons.
      self.elements = self.baseElements
      # initialise filename with songname and move to the end
      self.songNameEntry.insert(0,clist.songname)
      self.songNameEntry.xview_moveto(1)

   def buildBaseElements (self):
      """
         Constructs and returns the base elements of a SongRow and returns them.
      """
      output = []
      output.append(Button(self.master,text="✖", command=self.delete))
      # extra spacing because all objects get the same grid() args
      output.append(Label(self.master,text=" "))
      # down button
      output.append(Button(self.master,text="▼", command=lambda: self.master.moveSongDown(self.row-1)))
      # shows priority
      output.append(Label(self.master,textvariable=self.strRow))
      # up button
      output.append(Button(self.master,text="▲", command=lambda: self.master.moveSongUp(self.row-1)))
      # extra spacing because all objects get the same grid() args
      output.append(Label(self.master,text=" "))
      # open file for the song name
      output.append(Button(self.master,text="Open", command=self.openFile))
      # call updateName every time the entry is changed
      sv = StringVar()
      sv.trace("w", lambda name, index, mode: self.updateName())
      # the entry object itself
      self.songNameEntry = Entry(self.master, width=50, textvariable=sv)
      output.append(self.songNameEntry)
      # extra spacing, if you haven't figured out the pattern yet
      output.append(Label(self.master,text=" "))
      return output

   def clear (self):
      """
         Clears all elements of this row from the master grid.
      """
      for element in self.elements:
         element.grid_forget()

   def delete (self):
      """
         Deletes this row from master.
      """
      self.clear()
      self.master.pop(self.row-1)

   def updateName (self):
      """
         Sets the song name in the clist to the song name in songNameEntry. Called automatically whenever songNameEntry changes.

         Invokes callbacks for changes.
      """
      self.clist.songname = self.songNameEntry.get()
      self.master.callbacks()

   def update (self, callback=True):
      """
         Updates and draws this objects.

         Invokes callbacks for changes unless callback is specified as False.
      """
      self.strRow.set(str(self.row))
      for element in self.elements:
         element['state'] = 'normal'
         element.grid_forget()
      
      # disable arrows if the row is inappropriate
      if self.row == 1:
         self.baseElements[4]['state'] = 'disabled'
      if self.row == self.master.count():
         self.baseElements[2]['state'] = 'disabled'

      # construct condition buttons
      self.conditionButtons = [ConditionButton(self,index) for index in range(len(self.clist))]
      self.conditionButtons.append(ConditionButton(self,len(self)))
      # construct complete list of elements
      self.elements = self.baseElements + self.conditionButtons
      # draw elements
      for index in range(len(self.elements)):
         self.elements[index].grid(row=self.row,column=index,sticky=N+E+W+S,padx=2,pady=1)
      if callback:
         self.master.callbacks()

   def openFile (self):
      # get a file
      filename = filedialog.askopenfilename(filetypes = (("Music files", "*.mp3 *.ogg, *.flac *.m4a *.wav"),("All files","*")))
      # insert into songNameEntry (callback automatically invoked)
      self.songNameEntry.delete(0,END)
      self.songNameEntry.insert(0,filename)
      self.songNameEntry.xview_moveto(1)

   def pop (self, index=0):
      """
         Removes a Condition or Instruction object from the contained ConditionList.
      """
      temp = self.clist.pop(index)
      # call update, drawing and invoking calbacks
      self.update()
      return temp

   def append (self, element):
      """
         Adds a Condition or Instruction object to the end of the contained ConditionList.
      """
      self.clist.append(element)
      # call update, drawing and invoking callbacks
      self.update()

   def __getitem__ (self, index):
      """
         Provides clist access without directly using self.clist.
      """
      return self.clist[index]

   def __setitem__ (self, index, value):
      """
         Provides clist access without directly using self.clist.
      """
      self.clist[index] = value

   def __len__ (self):
      """
         Provides clist access without directly using self.clist.
      """
      return len(self.clist)

class SongEditor (Frame):
   def __init__ (self, master, clists = []):
      """
         Constructor.
      """
      # frame init
      super().__init__(master)
      # songrows is empty to start
      self.songrows = []
      self.newSongButton = Button(self,text="Add Song",command=self.addSong)
      self.registered = []
      # load clists into songrows as needed
      self.load(clists)
      # necessary callbacks: update previewer and update own information, whenever stuff changes
      self.register(master.updateCurrent)
      self.register(master.editor.updateEditor)

   def load (self, clists):
      """
         Load the given condition lists into the song editor.
      """
      # clear previous information
      for child in self.winfo_children():
         child.grid_forget()
      # reconstruct
      self.songrows = []
      # turn clists into song rows
      for index in range(len(clists)):
         self.songrows.append(SongRow(self,index+1,clists[index]))
      # update, but don't invoke callbacks, since loading a player's entries doesn't change the .4ccm
      self.update(True, False)

   def addSong (self):
      """
         Add a new empty song row.
      """
      self.songrows.append(SongRow(self,len(self.songrows)+1,ConditionList()))
      # update; only need to add headings if this was the first row
      self.update(len(self.songrows)==1)

   def callbacks (self):
      for callback in self.registered:
         callback()

   def update (self, headings = False, callback = True):
      """
         Updates every SongRow object and constructs surrounding elements as needed.
      """
      # update every song row
      for index in range(len(self.songrows)):
         songrow = self.songrows[index]
         songrow.row = index+1
         # don't invoke callbacks on a per-row basis, they'll be called at the end if needed
         songrow.update(callback=False)
      # check if we should add headings
      if len(self.songrows) > 0 and headings:
         Label(self,text="Priority").grid(row=0,column=2,columnspan=3,sticky=E+W)
         Label(self,text="Song Location").grid(row=0,column=6,columnspan=2,sticky=E+W)
         Label(self,text="Conditions").grid(row=0,column=9,columnspan=999,sticky=W)
      # move the new song button
      self.newSongButton.grid_forget()
      self.newSongButton.grid(row=len(self.songrows)+1,column=0,columnspan=3,sticky=E+W, padx=2, pady=2)
      # invoke callbacks if needed
      if callback:
         self.callbacks()

   def moveSongUp (self, index):
      """
         Moves the song at the given index up one place (decreases index).
      """
      temp = self.songrows.pop(index)
      self.songrows.insert(index-1,temp)
      self.update()

   def moveSongDown (self, index):
      """
         Moves the song at the given index down one place (increases index).
      """
      temp = self.songrows.pop(index)
      self.songrows.insert(index+1,temp)
      self.update()

   def pop (self, index=0):
      """
         Deletes the song at the given index.
      """
      temp = self.songrows.pop(index)
      self.update()
      return(temp)

   def clists (self):
      """
         Gets the current condition lists.

         It might be useful to call update() before this to make sure all information is up to date.
      """
      return [row.clist for row in self.songrows]

   def count (self):
      """
         Gets the number of SongRow objects managed in the object. Can't use __len__ because tkinter needs it.
      """
      return len(self.songrows)

   def register (self, callback):
      self.registered.append(callback)

class PlayerSelectFrame (Frame):
   def __init__ (self, editor, command = None, players = []):
      super().__init__(editor)
      
      self.newPlayerEntry = Entry(self, width=30)
      self.newPlayerEntry.grid(row=0,column=1, sticky=N+W,padx=5,pady=10)
      # songs for each player
      self.songs = {
         "Anthem" : [],
         "Victory Anthem" : [],
         "Goalhorn" : []
      }
      # create list selector with default options
      self.playerMenu = ScrollingListbox(self,exportselection=False)
      self.playerMenu.insert(END,"Anthem")
      self.playerMenu.insert(END,"Victory Anthem")
      self.playerMenu.insert(END,"Goalhorn")
      self.playerMenu.grid(row=2,column=0,padx=5,pady=5,sticky=N+S)
      self.current = None
      self.editor = editor
      # delete player
      buttonFrame = Frame(self)
      Button(buttonFrame, text="Add Player", command=self.addPlayer).pack(fill=X,pady=2)
      self.renameButton = Button(buttonFrame, text="Rename Selected", command=self.renamePlayer)
      self.renameButton.pack(fill=X,pady=2)
      self.deleteButton = Button(buttonFrame, text="Delete Selected", command=self.deletePlayer)
      self.deleteButton.pack(fill=X,pady=2)
      buttonFrame.grid(row=0,column=0,padx=5,pady=5)
      # create song editor
      self.songEditor = SongEditor(self)
      self.songEditor.grid(row=2,column=1,rowspan=3,sticky=NE+SW,padx=5,pady=5)
      # add any players passed to constructor
      self.updateList(players)
      # bind callback to list
      self.bindSelect(self.loadSongEditor)
      self.playerMenu.selection_set(first = 0)
      self.loadSongEditor("Anthem")

   def loadSongEditor (self, pname):
      """
         Sets the SongEditor to work with the given player name, and updates rename/delete buttons as needed.
      """
      if pname in specialNames:
         self.renameButton["state"] = 'disabled'
         self.deleteButton["state"] = 'disabled'
      else:
         self.renameButton["state"] = 'normal'
         self.deleteButton["state"] = 'normal'
      self.current = None
      clists = self.songs[pname]
      self.songEditor.load(clists)
      self.current = pname

   def updateCurrent (self):
      """
         Updates the current player information to the new clists.
      """
      if self.current is not None:
         self.songs[self.current] = self.songEditor.clists()

   def updateList (self, players = []):
      """
         Sets the list box contents to the reserved names plus the contents of players.
      """
      self.playerMenu.delete(3,END)
      players.sort()
      for player in players:
         self.playerMenu.insert(END,player)
      setMaxWidth(players+list(specialNames),self.playerMenu)

   def updateSongs (self, songs):
      """
         Loads the specified dict into this structure.

         Should only be needed at load time.
      """
      self.songs = {
         "Anthem" : [],
         "Victory Anthem" : [],
         "Goalhorn" : []
      }
      for player in self:
         if player in songs:
            self.songs[player] = songs[player]
         elif player not in specialNames:
            self.songs.delete(player)
      self.current = None
      self.loadSongEditor("Anthem")
      self.current = "Anthem"

   def addPlayer (self):
      """
         Inserts the value of newPlayerEntry into the Listbox.
      """
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
      self.songs[name] = []
      self.setSelection(i)

   def setSelection (self,index):
      """
         Setls the selection to the player at the given index.
      """
      self.playerMenu.selection_clear(first=0,last=END)
      self.playerMenu.selection_set(first=index)
      self.loadSongEditor(pname=self.get())

   def deletePlayer (self):
      """
         Deletes the selected player.
      """
      name = self.get()
      if name in specialNames:
         messagebox.showwarning("Error","Cannot delete special song type.")
         return
      self.playerMenu.delete(self.playerMenu.curselection()[0])
      self.setSelection(0)

   def renamePlayer (self):
      """
         Renames the currently selected player to the value of newPlayerEntry.
      """
      name = self.newPlayerEntry.get()
      oldname = self.get()
      if name == oldname: # we don't need to do anything so be silent
         return
      elif name in self:
         messagebox.showwarning("Error","Cannot rename to existing player {}.".format(name))
         return
      elif name == "":
         messagebox.showwarning("Error","Player name cannot be empty.")
         return
      temp = self.songEditor.clists()
      self.deletePlayer()
      self.addPlayer()
      self.songs[name] = temp
      self.current = None
      self.loadSongEditor(pname=name)

   def get (self):
      """
         Returns the currently selected value.
      """
      index = self.playerMenu.curselection()[0]
      return self.playerMenu.get(index)

   def __getitem__ (self, index):
      """
         Access to player items for iteration.
      """
      # need to do this manually otherwise tkinter starts appending empty items to the list
      if index < 0 or index >= self.playerMenu.size():
         raise IndexError
      return self.playerMenu.get(index)

   def bindSelect (self, command):
      """
         Binds the given callback to be invoked whenever the Listbox object changes its value.

         The command should take a single string argument, which will be the value selected in the box.
      """
      def eventToName (event):
         index = int(event.widget.curselection()[0])
         return event.widget.get(index)
      self.playerMenu.bind('<<ListboxSelect>>',lambda event, copy=command: copy(eventToName(event)))

class Preview4CCM (Frame):
   def __init__ (self, master, editor, **kwargs):
      super().__init__(master, editor, **kwargs)
      self.editor = editor
      self.buffer = StringIO()
      self.text = Text(self, state=DISABLED, width=60, bg="#f0f0ed")
      self.text.pack(fill=Y,expand=1)

   def update (self):
      self.buffer = StringIO()
      self.editor.writefile(self.buffer,silent=True)
      self.text['state'] = NORMAL
      self.text.delete(1.0,END)
      self.text.insert(1.0,self.buffer.getvalue())
      self.text['state'] = DISABLED

class Editor (Frame):
   def __init__ (self, master):
      # tkinter master window
      super().__init__(master)
      # save/load
      fileMenu = self.buildFileMenu()
      fileMenu.pack(anchor="nw")
      self.previewer = None
      # file name of the .4ccm
      self.filename = None
      # team name editor and previewer
      leftFrame = Frame(self, pady=5)
      temp = Frame(leftFrame)
      Label(temp, text="Team Name:").pack(side=LEFT)
      # this makes the editor update whenever team name is modified
      sv = StringVar()
      sv.trace("w", lambda name, index, mode: self.updateEditor())
      # create the actual entry object
      self.teamEntry = Entry(temp, width=20, textvariable=sv)
      self.teamEntry.pack(side=LEFT)

      # player menu
      self.playerMenu = PlayerSelectFrame(self)
      # previewer
      self.previewer = Preview4CCM(leftFrame,self)
      temp.pack(anchor="w")
      self.previewer.pack()
      # pack playermenu after leftFrame
      leftFrame.pack(anchor="nw",side=LEFT)
      self.playerMenu.pack(anchor="nw",side=LEFT)
      
   def buildFileMenu (self):
      """
         Constructs the file save/load menu buttons.
      """
      buttons = Frame(self)
      Button(buttons, text="New .4ccm", command=self.clear4ccm).pack(side=LEFT)
      Button(buttons, text="Load .4ccm", command=self.load4ccm).pack(side=LEFT)
      Button(buttons, text="Save .4ccm", command=self.save4ccm).pack(side=LEFT)
      Button(buttons, text="Save .4ccm As...", command=self.save4ccmas).pack(side=LEFT)
      return buttons

   def clear4ccm (self):
      self.filename = None
      self.teamEntry.delete(0,END)
      self.playerMenu.updateList([])
      self.playerMenu.updateSongs({})

   def updateEditor (self):
      if self.previewer is not None:
         self.previewer.update()

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
      self.updateEditor()

   def save4ccm (self):
      if self.filename is None:
         self.filename = filedialog.asksaveasfilename(defaultextension=".4ccm", filetypes = (("Rigdio export files", "*.4ccm"),("All files","*")))
      file = open(self.filename,'w')
      self.writefile(file)

   def save4ccmas (self):
      self.filename = filedialog.asksaveasfilename(defaultextension=".4ccm", filetypes = (("Rigdio export files", "*.4ccm"),("All files","*")))
      file = open(self.filename,'w')
      self.writefile(file)

   def writefile (self,outfile,silent=False):
      if self.teamEntry.get() == "" and outfile != self.previewer.buffer: # allow empty team name when writing to preview buffer
         messagebox.showerror("Error","Team name cannot be empty.")
         return None
   
      players = self.playerMenu.songs
      flag = False
      outConvert(players)
      print("# team identifier", file=outfile)
      print("name;{}".format(self.teamEntry.get()), file=outfile)
      print("",file=outfile)
      # if no victory anthems provided, copy normal anthem
      print("# reserved names", file=outfile)
      if outfile != self.previewer.buffer and ("victory" not in players or len(players["victory"]) == 0):
         players["victory"] = players["anthem"]
      for player in self.playerMenu:
         player = outName(player)
         if player not in reserved and flag == False:
            print("",file=outfile)
            print("# regular players", file=outfile)
            flag = True
         if len(players[player]) > 0:
            if not silent:
               print("Writing songs for player {}.".format(player))
            for conditions in players[player]:
               print("{};{}".format(player,conditions), file=outfile)
         else:
            if not silent:
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