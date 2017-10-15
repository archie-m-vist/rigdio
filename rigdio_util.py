# thanks to stackoverflow: http://stackoverflow.com/questions/27650712/python-time-in-format-dayshoursminutesseconds-to-seconds
def timeToSeconds(time):
   multi = [1,60,3600,86400]
   try:
      time = [float(x) for x in time.split(":")]
      t_ret = 0
      for i,t in enumerate(reversed(time)):
         t_ret += multi[i] * t
      return t_ret
   except ValueError:
      return None

def main():
   print(timeToSeconds("1:30"))
   print(timeToSeconds("0:40"))

if __name__ == '__main__':
   main()