import yaml
import os.path as path
from entry import AudioEntry

def processSongList (data, sharedSpace = None):
   if isinstance(data,list):
      output = []
      for item in data:
         if isinstance(item,dict):
            new = AudioEntry(**item, sharedSpace = sharedSpace)
         else:
            new = AudioEntry(filename=item, sharedSpace = sharedSpace)
         output.append(new)
   elif isinstance(data,dict):
      output = [AudioEntry(**data, sharedSpace = sharedSpace)]
   else:
      output = [AudioEntry(filename=data, sharedSpace = sharedSpace)]
   return output

def processListDict (data, sharedSpace = None):
   output = {}
   if isinstance(data,dict):
      for key in data.keys():
         output[key] = processSongList(data[key], sharedSpace)
   else:
      output["default"] = processSongList(data[key], sharedSpace)
   return output

def processClipDict (data, sharedSpace = None):
   """
      Handles a clip dictionary, used for events and shared space.
   """
   output = {}
   for key in data.keys():
      if isinstance(data[key],dict):
         output[key] = AudioEntry(**data[key], sharedSpace = sharedSpace)
      else:
         output[key] = AudioEntry(filename=data[key], sharedSpace = sharedSpace)
   return output

def loadYML (filename):
   with open(filename,"r") as infile:
      raw = yaml.load(infile)
   # get team name
   if "team" in raw:
      teamName = raw["team"]
   else:
      print("WARNING: No team name given in {}. Using file name.".format(path.basename(filename)))
      teamName = path.basename(filename)
   # construct shared space
   if "shared" in raw and raw["shared"] is not None:
      sharedSpace = processClipDict(raw["shared"])
   else:
      sharedSpace = None
   # handle anthems (required)
   anthems = processSongList(raw["anthem"], sharedSpace)
   # handle victory anthems
   if "victory" in raw and raw["victory"] is not None:
      victory = processSongList(raw["victory"], sharedSpace)
   # if no victory anthems are found, just make a copy of the original anthem list
   else:
      victory = [entry.clone() for entry in anthems]

   # handle goalhorns (required)
   goalhorns = processListDict(raw["goal"], sharedSpace)
   # handle chants
   chants = []
   if "chant" in raw and raw["chant"] is not None:
      chants = processSongList(raw["chant"], sharedSpace)
   # handle events
   events = {}
   if "event" in raw and raw["event"] is not None:
      for key in raw["event"]:
         events[key] = processClipDict(raw["event"][key], sharedSpace)

   # note return order of the components
   # shared space is not returned, as its purpose has been served during the load step
   return teamName, anthems, victory, goalhorns, chants, events

iList = set(["start", "pause", "end"])

def processSingleLine (line):
   """
      Processes a single .4ccm line for the legacy loader.

      The line should be already split by semicolons and begin with its filename.
   """
   filename = line.pop(0)
   conditions = []
   instructions = {}
   for segment in line:
      segment = segment.split(" ")
      # instruction
      if segment[0] in iList:
         instructions[segment[0]] = segment[1]
      # condition
      else:
         conditions.append({})
         if segment[0] == "not": # the only metacondition allowed in .4ccm
            tokens = [{segment[1] : segment[2:]}]
         elif len(segment) == 2:
            tokens = segment[1]
         else:
            tokens = segment[1:]
         conditions[-1][segment[0]] = tokens
   return AudioEntry(filename=filename, conditions=conditions, instructions=instructions)

def load4CCM (filename):
   with open(filename,"r") as infile:
      raw = infile.readlines()
   header = "#"
   # ignore all starting comments
   while len(header) == 0 or header[0] == "#":
      header = raw.pop(0)
      header = header.strip(" \r\n\t")   
   header = header.split(";")
   # get team name
   if header[0] is not "team":
      print("WARNING: No team name given in {}. Using file name.".format(path.basename(filename)))
      teamName = path.splitext(filename)[1]

   else:
      teamName = header[1]
   # initialise storage sections
   # .4ccm files do not support shared space or events!
   anthems = []
   victory = []
   goalhorns = {}
   chants = []
   buckets = {
      "anthem" : anthems,
      "victory" : victory,
      "chant" : chants
   }
   # iterate across lines
   for line in raw:
      line = line.strip(" \r\n\t")
      if len(line) == 0 or line[0] == "#":
         continue
      line = line.split(";")
      if line[0] in buckets: # reserved .4ccm name
         buckets[line[0]].append(processSingleLine(line[1:]))
      else: # goalhorn
         if line[0] == "goal":
            line[0] = "default"
         if line[0] not in goalhorns:
            goalhorns[line[0]] = []
         goalhorns[line[0]].append(processSingleLine(line[1:]))

   # clone anthems for victory
   if len(victory) == 0:
      victory = [entry.clone() for entry in anthems]

   # same return order as the YML parser, but events are not supported
   return teamName, anthems, victory, goalhorns, chants, None

class NaughtyParseException (ValueError):
   def __init__ (message, *args, **kwargs):
      super().__init__("Parser error: {}".format(message))

def parseFile (filename):
   parsers = {
      ".yml" : loadYML,
      ".4ccm" : load4CCM
   }
   basename, extension = path.splitext(filename)
   if extension not in parsers:
      raise NaughtyParseException("File type {} not supported.".format(extension))
   return parsers[extension](filename)