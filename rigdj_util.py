from tkinter import *
import tkinter.font
# thanks to https://stackoverflow.com/a/21831742 for this method
def setMaxWidth(stringList, element):
   """
      Sets a tkinter element to have width matching the largest string in stringlist.
   """
   f = tkinter.font.nametofont(element.cget("font"))
   zerowidth=f.measure("0")
   w=int(max([f.measure(i) for i in stringList])/zerowidth)+1

   element.config(width=w)

def uiName (player):
   uiNames = {
      "anthem" : "Anthem",
      "goal" : "Goalhorn",
      "victory" : "Victory Anthem",
   }
   if player in uiNames:
      return uiNames[player]
   else:
      return player

def outName (player):
   outNames = {
      "Anthem" : "anthem",
      "Goalhorn" : "goal",
      "Victory Anthem" : "victory",
   }
   if player in outNames:
      return outNames[player]
   else:
      return player

def uiConvert (players):
   """
      Converts a players dictionary read from a 4ccm file from keyword names to human-readable names.

      Note that this does NOT change the pname values inside the condition lists themselves.
   """
   for key in players.keys():
      temp = uiName(key)
      if temp != key:
         players[temp] = players[key]
         players.pop(key)

def outConvert (players):
   """
      Converts a players dictionary created in rigDJ from human-readable names to keyword names.
   """
   uiNames = {
      "Anthem" : "anthem",
      "Goalhorn" : "goal",
      "Victory Anthem" : "victory",
   }
   for key in players.keys():
      if key in uiNames:
         players[uiNames[key]] = players[key]
         players.pop(key)


class ScrollingListbox (Listbox):
   """
      Simple class that combines a Listbox and Scrollbar.
   """
   def __init__ (self, master, *args, bd=2, **kwargs):
      # we need yscrollcommand to sync to the scroll bar
      if "yscrollcommand" in kwargs:
         raise ValueError("Cannot create ScrollingListbox with yscrollcommand or bd set.")
      # create a frame
      self.frame = Frame(master, bd=bd, relief=SUNKEN)
      self.scrollbar = Scrollbar(self.frame)
      self.scrollbar.pack(side=RIGHT, fill=Y)
      # initialise self inside own frame, and set yscrollcommand
      super().__init__(self.frame, *args, bd=0, yscrollcommand=self.scrollbar.set, **kwargs)
      super().pack(fill=BOTH, expand=1)
      # tell scrollbar to control yview
      self.scrollbar.config(command=self.yview)

   def pack (self, *args, **kwargs):
      # let the frame handle all the actual geometry
      self.frame.pack(*args, **kwargs)

   def grid (self, *args, **kwargs):
      # as above
      self.frame.grid(*args, **kwargs)