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
   )
)

def genCfg ():
   try:
      file = open("rigdio.yml",'x')
   except:
      print("Config file already exists!")
      return
   yaml.dump(defaults, file, default_flow_style=False)

class ConfigValues:
   def __init__ (self):
      startLog("rigdio.log")
      self.loadCfg()   

   def checkCfg (self):
      for key in defaults:
         if key not in self.cfg:
            self.cfg[key] = defaults[key]
      try: 
         self.cfg['fade']['time'] = float(self.cfg['fade']['time'])
      except:
         print("rigdio.yml error: fade time must be number. using default value.")
         self.cfg['fade']['time'] = defaults['fade']['time']
      try:
         self.cfg['gameMinute'] = float(self.cfg['gameMinute'])
      except:
         print("rigdio.yml error: gameMinute must be number. using default value.")
         self.cfg['fade']['time'] = defaults['fade']['time']

   def loadCfg (self):
      try:
         with open("rigdio.yml") as cfgfile:
            self.cfg = yaml.load(cfgfile)
            self.checkCfg()
      except Exception as e: # error loading config file, use defaults
         print("Error loading config file: {}".format(str(e)))
         print("Default values will be used.")
         self.cfg = defaults

   def __getattr__ (self, key):
      return self.cfg[key]

if __name__ == '__main__':
   genCfg()
else:
   settings = ConfigValues()