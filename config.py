import yaml
from logger import startLog

defaults = dict(
   fade=dict(
      anthem=False,
      goalhorn=True,
      time=2
   ),
   colours=dict(
      home='#e0e0fc',
      away='#ffe0dd'
   ),
   chants=dict(
      repeats=False,
      perTeam=2,
      goalFade=True,
      goalDelay=20,
      minimum=5,
      maximum=85,
      delay=2
   ),
   gameMinute=6.67,
   level=dict(
      target = -20.0
   ),
   match="Group",
   event=dict(
      delay=dict(
         yellow=4,
         red=5
      )
   )
)

def genCfg ():
   try:
      file = open("rigdio.yml",'x')
   except:
      print("Config file already exists!")
      return
   yaml.dump(defaults, file, default_flow_style=False)

def recursiveDictCheck (d, defaultD, location):
   for key in defaultD:
      if key not in d:
         print("Key {} not found in {}. Default value will be used.".format(key, location))
         d[key] = defaultD[key]
         continue
      elif isinstance(defaultD[key],dict):
         if not isinstance(d,dict):
            print("Key {} at {} is not a dict. Default values will be used.".format(key, location))
            d[key] = defaultD[key]
            continue
         else:
            recursiveDictCheck(d[key],defaultD[key],location+":"+str(key))

class ConfigValues:
   def __init__ (self):
      startLog("rigdio.log")
      self.loadCfg()   

   def checkCfg (self):
      recursiveDictCheck(self.cfg, defaults, "rigdio.yml")
      mustBeNumber = ['fade:time','chants:perTeam','chants:goalDelay','chants:minimum','chants:maximum','chants:delay','gameMinute','level:target','event:delay:yellow','event:delay:red']
      for item in mustBeNumber:
         items = item.split(":")
         entry = self.cfg
         default = defaults
         oldEntry = None
         for item in items:
            oldEntry = entry
            entry = entry[item]
            default = default[item]
         try:
            float(entry)
         except ValueError:
            print("rigdio.yml error: {} must be number; using default value {}.".format(item, default))
            oldEntry[items[-1]] = default

   def loadCfg (self):
      try:
         with open("rigdio.yml") as cfgfile:
            self.cfg = yaml.load(cfgfile)
      except Exception as e: # error loading config file, use defaults
         print("Error loading config file:",e)
         print("Default values will be used.")
         self.cfg = defaults
         return
      try:
         self.checkCfg()
      except Exception as e:
         print("Error checking config file:",e)
         print("This is probably a bug, rather than a rigdio.yml problem, but it shouldn't be fatal.")
         print("Default values will be used.")
         self.cfg = defaults

   def __getattr__ (self, key):
      return self.cfg[key]

if __name__ == '__main__':
   genCfg()
else:
   settings = ConfigValues()