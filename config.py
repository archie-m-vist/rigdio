import yaml
from logger import startLog

defaults = dict(
   fade=2
)

try:
   with open("rigdio.yml") as cfgfile:
      cfg = yaml.load(cfgfile)
      checkCfg(cfg)
except: # error loading config file, use defaults
   cfg = defaults

def genCfg ():
   try:
      file = open("rigdio.yml",'x')
   except:
      print("Config file already exists!")
      return
   yaml.dump(defaults, file, default_flow_style=False)

def checkCfg ():
   startLog("rigdio.log")
   try: 
      cfg['fade'] = int(cfg['fade'])
   except:
      print("rigdio.yml error: fade must be integer. using default value.")
      cfg['fade'] = defaults['fade']

if __name__ == '__main__':
   genCfg()