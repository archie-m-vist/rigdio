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
