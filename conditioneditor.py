from condition import *
from tkinter import *
import tkinter.filedialog as filedialog
import tkinter.messagebox as messagebox
from tkinter.simpledialog import Dialog
import tkinter.font
from rigdj_util import *

class ConditionEditor (Frame):
   """
      Abstract class 
   """
   def __init__ (self, master, cond, conditionType, build = True):
      super().__init__(master)
      self.conditionType = conditionType
      if cond == None:
         temp = self.default()
      else:
         temp = cond.tokens()
      self.fields = []
      if build:
         self.build(temp)

   def default (self):
      """
      Gives the default tokens for this condition type.
      """
      raise NotImplementedError("ConditionEditor subclass must override default() method.")

   def build (self, tokens):
      """
      Creates all tkinter objects used to create the condition, placing all variables in self.fields()
      in the order they're read as tokens.
      """
      raise NotImplementedError("ConditionEditor subclass must override build() method.")

   def tokens (self):
      """
      Converts the self.fields array to the tokens passed to the conditionType constructor.

      It's not normally necessary to override this, as long as each field represents exactly one
      token.
      """
      return [str(x.get()) for x in self.fields]

   def validate (self):
      """
      Checks that all fields are correctly formatted. Only needs to be overridden if there are input restrictions.

      Returns True if all conditions are met, False if there is an error. Should also show a tkinter error message explaining any problems.
      """
      return True

   def result (self):
      """
      Uses self.conditionType and self.tokens() to build the final Condition object.
      Will only be called if validate() returns True.

      You never need to override this.
      """
      return self.conditionType(self.tokens())

   def getEditor (ctype):
      editors = {
         # standard conditions
         "goals" : GoalConditionEditor,
         "comeback" : lambda master,cond: EmptyConditionEditor(master,cond,ComebackCondition),
         "first" : lambda master,cond: EmptyConditionEditor(master,cond,FirstCondition),
         "opponent" : OpponentConditionEditor,
         "lead" : LeadConditionEditor,
         "match" : MatchConditionEditor,
         "home" : lambda master,cond: EmptyConditionEditor(master,cond,HomeCondition),
         "once" : lambda master,cond: EmptyConditionEditor(master,cond,OnceCondition),
         "every" : EveryConditionEditor,
         # meta conditions
         "not" : NotConditionEditor,
         # instructions
         "start" : StartInstructionEditor,
         "pause" : PauseInstructionEditor,
         "end" : EndInstructionEditor
      }
      return editors[ctype]

class EmptyConditionEditor (ConditionEditor):
   def __init__ (self, master, cond, ctype):
      super().__init__(master,cond,ctype)

   def default (self):
      return []

   def build (self, tokens):
      pass

class GoalConditionEditor (ConditionEditor):
   def __init__ (self, master, cond):
      super().__init__(master,cond,GoalCondition)
   
   def default (self):
      return ["==",2]

   def build (self, tokens):
      Label(self, text="Goals By Player").grid(row=0,column=0,sticky=W)
      # operator
      self.fields.append(StringVar())
      self.fields[0].set(tokens[0])
      operators = ["==", "!=", "<", ">", "<=", ">="]
      opSelector = OptionMenu(self, self.fields[0], *operators)
      setMaxWidth(operators, opSelector)
      opSelector.grid(row=0,column=1,sticky=W)
      # value
      self.fields.append(StringVar())
      self.fields[1].set(str(tokens[1]))
      countEntry = Entry(self, textvariable=self.fields[1])
      countEntry.grid(row=0,column=2,sticky=W)

   def validate (self):
      try: 
         int(self.fields[1].get())
      except:
         messagebox.showwarning("Input Error", "Goals instruction must be compared to an integer.")
         return False
      return True

class LeadConditionEditor (ConditionEditor):
   def __init__ (self, master, cond):
      super().__init__(master,cond,LeadCondition)

   def default (self):
      return [">",0]

   def build (self, tokens):
      Label(self, text="Team Ahead By").grid(row=0,column=0,sticky=W)
      # operator
      self.fields.append(StringVar())
      self.fields[0].set(tokens[0])
      operators = ["==", "!=", "<", ">", "<=", ">="]
      opSelector = OptionMenu(self, self.fields[0], *operators)
      setMaxWidth(operators, opSelector)
      opSelector.grid(row=0,column=1,sticky=W)
      # value
      self.fields.append(StringVar())
      self.fields[1].set(str(tokens[1]))
      countEntry = Entry(self, textvariable=self.fields[1])
      countEntry.grid(row=0,column=2,sticky=W)

   def validate (self):
      try: 
         int(self.fields[1].get())
      except:
         messagebox.showwarning("Input Error", "Lead instruction must be compared to an integer.")
         return False
      return True

class EveryConditionEditor (ConditionEditor):
   def __init__ (self, master, cond):
      super().__init__(master,cond,EveryCondition)

   def default (self):
      return [2]

   def build (self, tokens):
      Label(self, text="Every").grid(row=0,column=0,sticky=W)
      self.fields.append(StringVar())
      self.fields[0].set(str(tokens[0]))
      countEntry = Entry(self, textvariable=self.fields[0])
      countEntry.grid(row=0,column=1,sticky=W)
      Label(self, text="Goals By Player").grid(row=0,column=2,sticky=W)

class OpponentConditionEditor (ConditionEditor):
   def __init__ (self, master, cond):
      ConditionEditor.__init__(self,master,cond,OpponentCondition)

   def default (self):
      return [""]

   def build (self, tokens):
      Label(self, text="Opponent is Any Of").grid(row=0,column=0,sticky=W)
      self.fields.append(StringVar())
      self.fields[0].set(str(tokens[0]))
      Entry(self, textvariable=self.fields[0]).grid(row=0,column=1,sticky=W+E)

   def tokens (self):
      return self.fields[0].get().split(" ")

class MatchConditionEditor (ConditionEditor):
   def __init__ (self, master, cond):
      self.selector = {}
      self.buttons = {}
      ConditionEditor.__init__(self,master,cond,MatchCondition)

   def default (self):
      return []

   def build (self, tokens):
      checkerFrame = Frame(self)
      for i in range(len(MatchCondition.types)//2):
         key = MatchCondition.types[i]
         Label(checkerFrame,text=key).grid(row = i, column = 0)
         self.selector[key] = IntVar()
         self.buttons[key] = Checkbutton(checkerFrame,variable=self.selector[key])
         self.buttons[key].grid(row=i, column = 1)

         key = MatchCondition.types[i+len(MatchCondition.types)//2]
         Label(checkerFrame,text=key).grid(row = i, column = 2)
         self.selector[key] = IntVar()
         self.buttons[key] = Checkbutton(checkerFrame,variable=self.selector[key])
         self.buttons[key].grid(row=i, column = 3)
         i += 1
      if len(MatchCondition.types) % 2 != 0:
         key = MatchCondition.types[-1]
         Label(checkerFrame,text=key).grid(row = len(MatchCondition.types)//2, column = 0)
         self.selector[key] = IntVar()
         self.buttons[key] = Checkbutton(checkerFrame,variable=self.selector[key])
         self.buttons[key].grid(row=len(MatchCondition.types)//2, column = 1)
      checkerFrame.pack()
      Button(self, text="Toggle Knockouts", command=self.toggleKnockouts).pack()

   def tokens (self):
      output = []
      for key in MatchCondition.types:
         temp = self.selector[key]
         if temp.get() == 1:
            output.append(key)
      return output

   def toggleKnockouts (self):
      off = False
      for key in MatchCondition.knockout:
         if self.selector[key].get() == 0:
            off = True
            break
      for key in MatchCondition.knockout:
         if off:
            self.buttons[key].select()
         else:
            self.buttons[key].deselect()

class MetaConditionEditor (ConditionEditor):
   def __init__ (self, master, cond, conditionType):
      super().__init__(master,cond,conditionType,False)
      if cond == None:
         self.subconditions = self.default()
      else:
         self.subconditions = cond.subconditions()
      self.update()

   def tokens (self):
      temp = []
      for sc in self.subconditions[:-1]:
         temp.extend(sc.tokens())
         temp.append(",")
      if len(self.subconditions) > 0:
         temp.extend(self.subconditions[-1].tokens())
      print(temp)
      return temp

   def build (self, tokens):
      raise TypeError("MetaConditionEditor should use update(), not build().")

   def update (self):
      raise NotImplementedError("MetaConditionEditor subclass must override update().")

   def edit (self, index):
      condition = self.subconditions[index]
      try:
         self.subconditions[index] = ConditionDialog(self.master,condition,condition == None).condition
         print(self.subconditions)
      except Exception as e:
         print(e)
      self.update()

class NotConditionEditor (MetaConditionEditor):
   def __init__ (self, master, cond):
      super().__init__(master,cond,NotCondition)

   def default (self):
      return [None]

   def update (self):
      if self.button is not None:
         self.button.pack_forget()
      if self.subconditions[0] == None:
         text = "Add Condition"
      else:
         text = str(self.subconditions[0])
      self.button = Button(self, text=text, command=lambda: self.edit(0))
      self.button.pack()

   def validate (self):
      if not self.subconditions[0].isInstruction():
         return True
      else:
         messagebox.showwarning("Input Error", "Not condition cannot be applied to an Instruction.")
         return False

class StartInstructionEditor (ConditionEditor):
   def __init__ (self, master, cond):
      super().__init__(master,cond,StartInstruction)

   def default (self):
      return ["0:00"]

   def build (self, tokens):
      Label(self, text="Start Playback At").grid(row=2,column=0,sticky=W)
      self.fields.append(StringVar())
      timeEntry = Entry(self, textvariable=self.fields[0])
      timeEntry.grid(row=2,column=1,sticky=W+E)

   def validate (self):
      if timeToSeconds(self.fields[0].get()) is None:
         messagebox.showwarning("Input Error", "Start instruction requires a time formatted as any of: day:hour:min:sec, hour:min:sec, min:sec, or sec.")
         return False

class PauseInstructionEditor (ConditionEditor):
   def __init__ (self, master, cond):
      super().__init__(master,cond,PauseInstruction)

   def default (self):
      return ["continue"]

   def build (self, tokens):
      self.fields.append(StringVar())
      self.fields[0].set(tokens[0])
      selector = OptionMenu(self, self.fields[0], *PauseInstruction.types)
      setMaxWidth(PauseInstruction.types, selector)
      selector.pack()

class EndInstructionEditor (ConditionEditor):
   def __init__ (self, master, cond):
      super().__init__(master,cond,EndInstruction)

   def default (self):
      return ["loop"]

   def build (self, tokens):
      self.fields.append(StringVar())
      self.fields[0].set(tokens[0])
      selector = OptionMenu(self, self.fields[0], EndInstruction.types)
      setMaxWidth(EndInstruction.types, selector)
      selector.pack()

class ConditionDialog (Dialog):
   def __init__ (self, master, condition, new = False):
      self.condition = condition
      self.master = master
      # UI information
      self.fields = []
      self.elements = []
      # check if new 
      self.new = new
      self.editor = None
      Dialog.__init__(self,master,"Editing Condition")

   def body (self, frame):
      self.conditionType = StringVar()
      self.conditionType.set("")
      if self.condition is not None:
         self.conditionType.set(self.condition.type())
      # condition type selector
      conditionTypeMenu, self.conditionDescLabel = self.buildConditionTypeMenu(frame)
      conditionTypeMenu.pack()
      self.editFrame = Frame(frame)
      self.editFrame.pack()
      self.changeConditionType(self.conditionType.get(),False)

   def buildConditionTypeMenu (self, frame):
      """
         Builds the condition type selector and docstring menu.
      """
      frame = Frame(frame)
      selectorFrame = Frame(frame)
      Label(selectorFrame, text="Condition Type", font="-weight bold").pack(side=LEFT)
      ctypes = list(conditions.keys())
      ctypes.sort()
      selector = OptionMenu(selectorFrame, self.conditionType, *ctypes, command=self.changeConditionType)
      setMaxWidth(ctypes,selector)
      selector.pack(side=LEFT)
      selectorFrame.pack()
      # condition description
      descLabelFrame = Frame(frame)
      descLabel = Label(descLabelFrame, text="", anchor=W, justify=LEFT, wraplength="10c")
      descLabel.pack()
      Label(descLabelFrame, text="", width=60).pack()
      descLabelFrame.pack()
      return frame, descLabel

   def validate (self):
      return self.editor.validate()

   def apply (self):
      # set condition variable to be retrieved
      if self.editor is not None:
         self.condition = self.editor.result()
      else:
         self.condition = None

   def buttonbox(self):
        box = Frame(self)

        w = Button(box, text="OK", width=10, command=self.ok, default=ACTIVE)
        w.pack(side=LEFT, padx=5, pady=5)
        if not self.new:
           w = Button(box, text="Delete", width=10, command=self.delete)
           w.pack(side=LEFT, padx=5, pady=5)
        w = Button(box, text="Cancel", width=10, command=self.cancel)
        w.pack(side=LEFT, padx=5, pady=5)

        self.bind("<Return>", self.ok)
        self.bind("<Escape>", self.cancel)
        self.bind("<Delete>", self.delete)

        box.pack(side=BOTTOM)

   def delete (self):
      self.condition = -1
      self.cancel()

   def changeConditionType (self, value, resetTokens = True):
      # reset existing editor
      if self.editor is not None:
         self.editor.pack_forget()
         self.editor = None
      
      # update description label
      if value == "":
         self.conditionDescLabel['text'] = "No condition type selected."
      else:
         self.conditionDescLabel['text'] = conditions[value].desc

      # if a type is selected, build an editor
      if value != "":
         self.editor = ConditionEditor.getEditor(value)(self.editFrame,self.condition)
         self.editor.pack()
      