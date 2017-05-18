from os.path import isfile

from tkinter import filedialog, Tk

import pyglet
from pyglet_gui.theme import Theme
from pyglet_gui.gui import Label
from pyglet_gui.manager import Manager
from pyglet_gui.buttons import Button, OneTimeButton
from pyglet_gui.containers import VerticalContainer

from rigparse import parse
from gamestate import GameState

import sys
sys.stdout = open('rigdio.log', 'w')
sys.stderr = sys.stdout

window = pyglet.window.Window(640, 480, resizable=True, vsync=True)
batch = pyglet.graphics.Batch()

root = Tk()
root.withdraw()

thome = Theme({"font": "Lucida Grande",
               "font_size": 12,
               "text_color": [211, 213, 215, 255],
               "gui_color": [0, 0, 255, 255],
               "button": {
                  "down": {
                     "image": {
                        "source": "button-down.png",
                        "frame": [8, 6, 2, 2],
                        "padding": [18, 18, 8, 6]
                     },
                     "text_color": [0, 0, 0, 255]
                  },
                  "up": {
                     "image": {
                        "source": "button.png",
                        "frame": [6, 5, 6, 3],
                        "padding": [18, 18, 8, 6]
                     }
                  }
               }},
               resources_path='theme/')
taway = Theme({"font": "Lucida Grande",
               "font_size": 12,
               "text_color": [211, 213, 215, 255],
               "gui_color": [255, 0, 0, 255],
               "button": {
                  "down": {
                     "image": {
                        "source": "button-down.png",
                        "frame": [8, 6, 2, 2],
                        "padding": [18, 18, 8, 6]
                     },
                     "text_color": [0, 0, 0, 255]
                  },
                  "up": {
                     "image": {
                        "source": "button.png",
                        "frame": [6, 5, 6, 3],
                        "padding": [18, 18, 8, 6]
                     }
                  }
               }},
               resources_path='theme/')
tsyst = Theme({"font": "Lucida Grande",
               "font_size": 12,
               "text_color": [211, 213, 215, 255],
               "gui_color": [0, 255, 0, 255],
               "button": {
                  "down": {
                     "image": {
                        "source": "button-down.png",
                        "frame": [8, 6, 2, 2],
                        "padding": [18, 18, 8, 6]
                     },
                     "text_color": [0, 0, 0, 255]
                  },
                  "up": {
                     "image": {
                        "source": "button.png",
                        "frame": [6, 5, 6, 3],
                        "padding": [18, 18, 8, 6]
                     }
                  }
               }},
               resources_path='theme/')

@window.event
def on_draw():
   window.clear()
   batch.draw()

game = GameState()

class PlayerButton (Button):
   def __init__ (self, name, data, home):
      Button.__init__(self,name,False,None)
      self.conditions = data
      self.song = None
      self.name = name
      self.home = home

   def on_mouse_press (self, x, y, button, modifiers):
      Button.on_mouse_press(self, x, y, button, modifiers)
      if ( self.is_pressed ):
         # update score
         game.score(self.name, self.home)
         # check conditions
         for condition in self.conditions:
            if ( condition.check(game) ):
               self.song = condition
               print("Playing",condition.songname)
               self.song.play()
               break
      else:
         # pause song
         if ( self.song is not None ):
            self.song.pause()
            self.song = None

def open_home_file(is_pressed):
   f = filedialog.askopenfilename(filetypes = (("Rigdio export files", "*.4ccm"),("All files","*.*")))
   if ( isfile(f) ):
      print("Loading music from "+f)
      home = parse(f)

      # reset buttons
      initHomeButtons()
      
      # get anthem and victory anthem
      homeButtons.add(Label("Anthems"))
      temp = home.pop('anthem', None)
      if ( temp != None ):
         homeButtons.add(PlayerButton('Anthem',temp,True))
      else:
         print("ERROR: no anthem specified in "+f+".")
      temp = home.pop('victory', None)
      if ( temp != None ):
         homeButtons.add(PlayerButton('Victory Anthem',temp,True))

      homeButtons.add(Label("Goalhorns"))
      # get default goalhorn
      temp = home.pop('goal', None)
      defaultGoal = None
      if ( temp != None ):
         defaultGoal = PlayerButton('Other',temp,True)
      else:
         print("ERROR: no default goalhorn specified in "+f+".")

      # iterate across player names
      for name, data in home.items():
         homeButtons.add(PlayerButton(name,data,True))

      if ( defaultGoal != None ):
         homeButtons.add(defaultGoal)

def open_away_file(is_pressed):
   f = filedialog.askopenfilename(filetypes = (("Rigdio export files", "*.4ccm"),("All files","*.*")))
   if ( isfile(f) ):
      print("Loading music from "+f)
      away = parse(f)

      # reset Manager
      initAwayButtons()
      
      # get anthem and victory anthem
      awayButtons.add(Label("Anthems"))
      temp = away.pop('anthem', None)
      if ( temp != None ):
         awayButtons.add(PlayerButton('Anthem',temp,False))
      else:
         print("ERROR: no anthem specified in "+f+".")
      temp = away.pop('victory', None)
      if ( temp != None ):
         awayButtons.add(PlayerButton('Victory Anthem',temp,False))


      awayButtons.add(Label("Goalhorns"))
      # get default goalhorn
      temp = away.pop('goal', None)
      defaultGoal = None
      if ( temp != None ):
         defaultGoal = PlayerButton('Other',temp,False)
      else:
         print("ERROR: no default goalhorn specified in "+f+".")

      # iterate across player names
      for name, data in away.items():
         awayButtons.add(PlayerButton(name,data,False))

      if ( defaultGoal != None ):
         awayButtons.add(defaultGoal)

homeButtons = None
awayButtons = None
homeManager = None
awayManager = None

# initialise home buttons, manager
def initHomeButtons ():
   button_home = OneTimeButton('Load Home Team Export', on_release=open_home_file)
   global homeButtons
   homeButtons = VerticalContainer([Label("Home Team"),button_home])
   global homeManager
   if ( homeManager != None ):
      homeManager.delete()
   homeManager = Manager(homeButtons,window=window,batch=batch,theme=thome,offset=(-150,70))

# initialise away buttons, manager
def initAwayButtons ():
   button_away = OneTimeButton('Load Away Team Export', on_release=open_away_file)
   global awayButtons
   awayButtons = VerticalContainer([Label("Away Team"),button_away])
   global awayManager
   if ( awayManager != None ):
      awayManager.delete()
   awayManager = Manager(awayButtons,window=window,batch=batch,theme=taway,offset=(150,70))

def clearGameState (is_pressed):
   game.clear()

def main ():
   initHomeButtons()
   initAwayButtons()
   Manager(OneTimeButton('Reset Game State',on_release=clearGameState),window=window, batch=batch,theme=tsyst,offset=(0,-200))
   try:
      pyglet.app.run()
   except:
      close(sys.stdout)

if __name__ == '__main__':
   main()