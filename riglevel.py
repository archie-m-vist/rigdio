import sys, os
from pydub import AudioSegment
from config import settings

AudioSegment.converter = os.path.join(os.path.dirname(sys.argv[0]),"libav\\avconv.exe")
if os.path.exists(AudioSegment.converter):
   print("Located avconv in riglevel libav folder.")

def main ():
   if len(sys.argv) == 1:
      print("No files provided; exiting.")
      return
   for file in sys.argv[1:]:
      print("Processing file {}".format(file))
      fname, ext = os.path.splitext(file)
      print(fname)
      ext = ext[1:]
      print("   File format is {}".format(ext))
      # get output directory
      outpath = os.path.join(os.path.dirname(file),"riglevel_out")
      
      if not os.path.exists(outpath):
         print("   Created output directory {}".format(outpath))
         os.makedirs(outpath)
      elif not os.path.isdir(outpath):
         print("   Output destination {} is not a directory, skipping.".format(outpath))
         continue
      else:
         print(   "Output will be placed in {}".format(outpath))
      sound = AudioSegment.from_file(file,format=ext)
      change = settings.level["target"] - sound.dBFS
      print("   File has volume {} dBFS, target is {} dBFS; applying {} dBFS gain.".format(sound.dBFS,settings.level["target"],change))
      output = sound.apply_gain(change)
      # export finished sound
      outfile = os.path.join(outpath,os.path.basename(fname)+".mp3")
      print("   Writing normalised file to {}".format(outfile))
      output.export(outfile,"mp3")
   print("Press Enter to continue.")
   char = input()

if __name__ == '__main__':
   try:
      main()
   except Exception as e:
      print(type(e).__name__,e)
      char = input()