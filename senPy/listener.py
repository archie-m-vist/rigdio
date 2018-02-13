class SENPAIListener:
   """
      Interface class for objects which listen to multithreaded SENPAI API.
   """

   def __init__ (self, *args, **kwargs):
      """
         Constructs the object. Call this at the end of your regular constructor!
      """
      self.eventHandlers = {
            "Teams Changed" : self.handleTeamsChangedEvent,
            "Goal" : self.handleGoalEvent,
            "Clock Started" : self.handleClockStartedEvent,
            "Clock Stopped" : self.handleClockStoppedEvent,
            "Stats Found" : self.handleStatsFoundEvent,
            "Stats Lost" : self.handleStatsLostEvent,
            "Card" : self.handleCardEvent,
            "Player Sub" : self.handlePlayerSubEvent,
            "Own Goal" : self.handleOwnGoalEvent
      }
      super().__init__(*args, **kwargs)

   def handleEvent (self, event):
      """
         Checks if an event is appropriate for this class to handle, then calls the appropriate handler.
         Override this only if you want to treat every single event object the same way.

         This function is called by ThreadSENPAI in its own thread; note that modifying the event object can cause unsafe behaviour!
         In general you should be treating the event objects as read-only, as there is no guarantee what other listeners might need them for.
      """
      if self.handlesEvent(event.event):
         self.eventHandlers[event.event](event)

   def handlesEvent(self, eventType):
      """
         Returns True if this class has the appropriate handleEvent function for a given event type (as given in SENPAI spec), otherwise False.

         All SENPAIListener objects must override this function.
      """
      raise NotImplementedException("SENPAIListener object must properly implement handlesEvent().")

   def handleTeamsChangedEvent (self, event):
      """Handles events of type Teams Changed. Will only be called if handlesEvent() returns True for Teams Changed events."""
      raise NotImplementedException("SENPAIListener object must properly implement handleTeamsChangedEvent, or return False from handlesEvent() for event type 'Teams Changed'.")


   def handleGoalEvent (self, event):
      """Handles events of type Goal. Will only be called if handlesEvent() returns True for Goal events."""
      raise NotImplementedException("SENPAIListener object must properly implement handleGoalEvent, or return False from handlesEvent() for event type 'Goal'.")


   def handleClockStartedEvent (self, event):
      """Handles events of type Clock Started. Will only be called if handlesEvent() returns True for Clock Started events."""
      raise NotImplementedException("SENPAIListener object must properly implement handleClockStartedEvent, or return False from handlesEvent() for event type 'Clock Started'.")


   def handleClockStoppedEvent (self, event):
      """Handles events of type Clock Stopped. Will only be called if handlesEvent() returns True for Clock Stopped events."""
      raise NotImplementedException("SENPAIListener object must properly implement handleClockStoppedEvent, or return False from handlesEvent() for event type 'Clock Stopped'.")


   def handleStatsFoundEvent (self, event):
      """Handles events of type Stats Found. Will only be called if handlesEvent() returns True for Stats Found events."""
      raise NotImplementedException("SENPAIListener object must properly implement handleStatsFoundEvent, or return False from handlesEvent() for event type 'Stats Found'.")


   def handleStatsLostEvent (self, event):
      """Handles events of type Stats Lost. Will only be called if handlesEvent() returns True for Stats Lost events."""
      raise NotImplementedException("SENPAIListener object must properly implement handleStatsLostEvent, or return False from handlesEvent() for event type 'Stats Lost'.")


   def handleCardEvent (self, event):
      """Handles events of type Card. Will only be called if handlesEvent() returns True for Card events."""
      raise NotImplementedException("SENPAIListener object must properly implement handleCardEvent, or return False from handlesEvent() for event type 'Card'.")


   def handlePlayerSubEvent (self, event):
      """Handles events of type Player Sub. Will only be called if handlesEvent() returns True for Player Sub events."""
      raise NotImplementedException("SENPAIListener object must properly implement handlePlayerSubEvent, or return False from handlesEvent() for event type 'Player Sub'.")


   def handleOwnGoalEvent (self, event):
      """Handles events of type Own Goal. Will only be called if handlesEvent() returns True for Own Goal events."""
      raise NotImplementedException("SENPAIListener object must properly implement handleOwnGoalEvent, or return False from handlesEvent() for event type 'Own Goal'.")

