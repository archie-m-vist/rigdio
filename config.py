import yaml
from logger import startLog

defaults = dict(
   fade=2,
   colours=dict(
      home='#e0e0fc',
      away='#ffe0dd'
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
         self.cfg['fade'] = float(self.cfg['fade'])
      except:
         print("rigdio.yml error: fade must be number. using default value.")
         self.cfg['fade'] = defaults['fade']

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

settings = ConfigValues()

if __name__ == '__main__':
   genCfg()