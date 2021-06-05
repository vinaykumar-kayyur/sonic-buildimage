from swsscommon import swsscommon
import time
import enum
import time
import os

class EvAction(enum.Enum):
     NOTIFY = 0
     CLEAR_ALARM = 1
     RAISE_ALARM = 2
     ACK_ALARM = 3
     UNACK_ALARM = 4

class EventNotify:
    def __init__(self):
        """Create a new Event Notify class."""
        self.event_db = swsscommon.DBConnector("EVENT_DB", 0, True)
        self.evntPubTbl = swsscommon.Table(self.event_db, "EVENTPUBSUB")
        self.evProfileTbl = swsscommon.Table(self.event_db, "EVPROFILE")
        self.evntStateTbl = swsscommon.Table(self.event_db, "EVENT_STATS")
        self.almStateTbl = swsscommon.Table(self.event_db, "ALARM_STATS")
        self.sequence_id = 0

    def getTicks(self):
        return (time.time_ns())

    def getActionStr(self, action):
        if action ==  EvAction.CLEAR_ALARM:
            return "CLEAR"
        elif action ==  EvAction.RAISE_ALARM:
            return "RAISE"
        elif action ==  EvAction.ACK_ALARM:
            return "ACKNOWLEDGE"
        elif action ==  EvAction.UNACK_ALARM:
            return "UNACKNOWLEDGE"
        else: 
            return ""

    def logevent(self, name, source, action, message):
        self.sequence_id = self.sequence_id + 1
        key = name + str(self.sequence_id)
        actionStr = self.getActionStr(action)
        fvs = swsscommon.FieldValuePairs([("time-created", str(self.getTicks())), ("type-id", name), ("text", message), ("action", actionStr), ("resource", source)])
        self.evntPubTbl.set(key, fvs)
