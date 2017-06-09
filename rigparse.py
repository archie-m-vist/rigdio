import os
import vlc

from os.path import basename, splitext
from condition import ConditionList, ConditionPlayer, loadsong

# reserved names
reserved = set(['anthem', 'victory', 'goal', 'name'])

"""Parses a music export file and loads it into memory."""
def parse (filename, load = True, home = True):
   # get location of folder
   folder = '/'.join(filename.split('/')[0:-1])+'/'
   output = {}
   filenames = {
      "goal" : "Goalhorn",
      "anthem" : "Anthem",
      "victory" : "Victory Anthem"
   }
   
   # open filename
   with open(filename) as f:
      lines = [line.strip() for line in f.readlines()]
      f.close()

   # get name
   while len(lines[0]) == 0 or lines[0][0] == '#':
      lines = lines[1:]
   nameline = lines[0].split(';')
   if len(nameline) < 2 or nameline[0] != "name":
      print("No team name provided at start of file; defaulting to filename")
      tname = splitext(basename(filename))[0]
   else:
      tname = nameline[1].lower()
      lines = lines[1:]

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
      if len(data) == 1:
         default = "{} - {}.mp3" if player in reserved else "{} - {} Goalhorn.mp3"
         fancyname = filenames[player] if player in reserved else player
         default = default.format(tname,fancyname)
         print("No file name specified for {}, looking for {}.".format(player, default))
         data.append(default)

      filename = folder+data[1] # location of song, relative to location of export file
      if load:
         clist = ConditionPlayer(data[0], tname, data[2:], filename, home, loadsong(filename,player=='victory'), (player != "anthem" and player != "victory"))
      else:
         clist = ConditionList(data[0], tname, data[2:], filename, home)
      output[player].append(clist)
   
   # copy default goalhorn onto the end of all player goalhorns
   if load:
      for name, conditions in output.items():
         if ( name not in reserved ):
            output[name].extend(output['goal'])
   print("Loaded songs for team /{}/".format(tname))
   return output, tname

def main ():
   file = parse("./music/4cc/m/m.4ccm")
   file["Char's Zaku II"][0].song.play()
   i = 0
   time.sleep(15)
   file["Char's Zaku II"][0].song.pause()
   time.sleep(5)
   file["Char's Zaku II"][0].song.play()
   while True:
      pass

if __name__ == '__main__':
   import time
   main()