from tkinter import *
import tkinter.filedialog as filedialog
import tkinter.font
from rigparse import parse

from logger import Logger
from rigdj_util import *

sys.stdout = Logger("rigdj.log")
sys.stderr = sys.stdout

master = Tk()
master.minsize(640,480)

team = StringVar(master)
team.set("No Team Loaded")

player = StringVar(master)
player.set("")

filename = None

players = {}
name = Entry(master)
name.grid(row=1,column=1)
playerMenu = OptionMenu(master,player,"Anthem","Goalhorn","Victory Anthem")
setMaxWidth(["Anthem","Goalhorn","Victory Anthem"],playerMenu)
playerMenu.grid(row = 2, column = 1)

Label(master, text="Team:", font="-weight bold").grid(row=1,column=0,sticky=E)

def load4ccm ():
   global playerMenu, players, name, filename
   filename = filedialog.askopenfilename(filetypes = (("Rigdio export files", "*.4ccm"),("All files","*")))
   players, teamName = parse(filename,False)
   uiConvert(players)

   name.delete(0,END)
   name.insert(0,teamName)

   # add player menu and "add player" button if not already present
   if playerMenu is not None:
      playerMenu.grid_forget()
   playerMenu = OptionMenu(*((master,player)+tuple(sorted(list(players.keys())))))
   setMaxWidth(players,playerMenu)
   playerMenu.grid(row = 2, column = 1)

def writefile (filename):
   with open(filename, 'w') as outfile:
      print("name;{}".format(name.get()), file=outfile)
      outConvert(players)
      for key in players.keys():
         print(key)
         for conditions in players[key]:
            print("{};{}".format(key,conditions), file=outfile)

def save4ccm ():
   global filename
   if filename is None:
      filename = filedialog.asksaveasfilename(filetypes = (("Rigdio export files", "*.4ccm"),("All files","*")))
   writefile(filename)
   

def save4ccmas ():
   global filename
   filename = filedialog.asksaveasfilename(filetypes = (("Rigdio export files", "*.4ccm"),("All files","*")))
   writefile(filename)

def newplayer ():
   print("Adding player!")

playerEntry = Entry(master)
playerEntry.grid(row = 2,column = 2)
playerButton = Button(master, text="Add Player", command=newplayer)
playerButton.grid(row = 2, column = 3)
Label(master, text="Player:", font="-weight bold").grid(row=2,column = 0,sticky=W)

loadButton = Button(master, text="Load .4ccm", command=load4ccm)
loadButton.grid(row = 0, column = 0)
loadButton = Button(master, text="Save .4ccm", command=save4ccm)
loadButton.grid(row = 0, column = 1)
loadButton = Button(master, text="Save .4ccm As...", command=save4ccmas)
loadButton.grid(row = 0, column = 2)

mainloop()