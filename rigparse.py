import os
import pyglet
from os.path import abspath, isfile
from condition import ConditionList

def loadsong(filename):
   print("Attempting to load "+filename)
   filename = abspath(filename)
   if not ( isfile(filename) ):
      raise Exception(filename+" not found.")
   song = pyglet.media.load(filename)
   source = song.play()
   source.pause()
   return source

"""Parses a music export file and loads it into memory."""
def parse (filename):
   # get location of folder
   folder = '/'.join(filename.split('/')[0:-1])+'/'
   pyglet.resource.path.append(folder)
   output = {}
   # open filename
   with open(filename) as f:
      lines = [line.strip() for line in f.readlines()]
   # iterate across lines
   for line in lines:
      # ignore comments
      if len(line) == 0 or line[0] == "#":
         continue
      # split up line by ;
      data = line.split(';')  
      player = data[0] # name of player
      if player not in output:
         output[player] = []
      filename = folder+data[1] # location of song, relative to location of export file
      clist = ConditionList(data[0], loadsong(filename), filename, data[2:])
      output[player].append(clist)
   # copy default goalhorn onto the end of all player goalhorns
   reserved = ['anthem', 'victory', 'goal'] # reserved names
   for name, conditions in output.items():
      if ( name not in reserved ):
         output[name].extend(output['goal'])
   return output

def main ():
   mSongs = parse("./music/m/m.4ccm")
   for player in mSongs:
      print(player)
      for condition in mSongs[player]:
         print(" - "+str(condition))
   mSongs['Alteisen Riese'][0].song.play()
   pyglet.app.run()

if __name__ == '__main__':
   main()