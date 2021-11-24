from eventnotify import eventnotify
from swsscommon import swsscommon
import time
import enum
import time
import os
import json

class EventUnitTest:
    def unittest_init(self):
        self.event_db = swsscommon.DBConnector("EVENT_DB", 0, True)
        self.eventTbl = swsscommon.Table(self.event_db, "EVENT")
        self.alarmTbl = swsscommon.Table(self.event_db, "ALARM")
        self.eventStateTbl = swsscommon.Table(self.event_db, "EVENT_STATS")
        self.alarmStateTbl = swsscommon.Table(self.event_db, "ALARM_STATS")
        self.evProfileTbl = swsscommon.Table(self.event_db, "EVPROFILE")
        self.notify = eventnotify.EventNotify()

    def test_event(self):
        print("\nTEST: raise event")
        eventCount = 0
        newEventCount = 0
        fvs = 0
        (status, fvs) = self.eventStateTbl.get("state")
        for fv in fvs:
            if fv[0] == "events":
                eventCount = int(fv[1])

        self.notify.logevent("CUSTOM_EVPROFILE_CHANGE", "x.json", eventnotify.EvAction.NOTIFY, "Raised for unit testing")
        time.sleep(0.2)
        (status, fvs) = self.eventStateTbl.get("state")
        for fv in fvs:
            if fv[0] == "events":
                newEventCount = int(fv[1])
        if (eventCount+1) == newEventCount:
            print("test_event success")
        else:
            print("ERROR: test_event failed" + " " + str(eventCount) + " " + str(newEventCount))

    def raise_alarm(self):
        print("\nTEST: raise alarm")
        raisedCount = 0
        newRaisedCount = 0
        fvs = 0
        (status, fvs) = self.eventStateTbl.get("state")
        for fv in fvs:
            if fv[0] == "raised":
                raisedCount = int(fv[1])

        (status, fvs) = self.alarmStateTbl.get("state")
        for fv in fvs:
            if fv[0] == "alarms":
                alarmCount = int(fv[1])
            if fv[0] == "warning":
                warningCount = int(fv[1])

        self.notify.logevent("DUMMY_ALARM", "test_raise_alarm", eventnotify.EvAction.RAISE_ALARM, "Raised for unit testing")
        time.sleep(0.2)

        (status, fvs) = self.eventStateTbl.get("state")
        for fv in fvs:
            if fv[0] == "raised":
                newRaisedCount = int(fv[1])

        (status, fvs) = self.alarmStateTbl.get("state")
        for fv in fvs:
            if fv[0] == "alarms":
                newAlarmCount = int(fv[1])
            if fv[0] == "warning":
                newWarningCount = int(fv[1])

        if (raisedCount+1) == newRaisedCount:
            if (alarmCount + 1) == newAlarmCount:
                if (warningCount + 1) == newWarningCount:
                    print("test_raise_alarm success")
                else:
                    print("ERROR: test_raise_alarm severity count failed" + " " + str(warningCount) + " " + str(newWarningCount))
            else:
                print("ERROR: test_raise_alarm alarm count failed" + " " + str(alarmCount) + " " + str(newAlarmCount))
        else:
            print("ERROR: test_raise_alarm event count failed" + " " + str(raisedCount) + " " + str(newRaisedCount))

        self.notify.logevent("DUMMY_ALARM", "test_raise_alarm", eventnotify.EvAction.CLEAR_ALARM, "Clearing for unit testing")
        time.sleep(0.2)

    def clear_alarm(self):
        print("\nTEST: raise and clear alarm")
        self.notify.logevent("DUMMY_ALARM", "test_clear_alarm", eventnotify.EvAction.RAISE_ALARM, "Raised for unit testing")
        time.sleep(0.2)
        clearCount = 0
        newClearCount = 0
        fvs = 0
        (status, fvs) = self.eventStateTbl.get("state")
        for fv in fvs:
            if fv[0] == "cleared":
                clearCount = int(fv[1])

        (status, fvs) = self.alarmStateTbl.get("state")
        for fv in fvs:
            if fv[0] == "alarms":
                alarmCount = int(fv[1])
            if fv[0] == "warning":
                warningCount = int(fv[1])

        self.notify.logevent("DUMMY_ALARM", "test_clear_alarm", eventnotify.EvAction.CLEAR_ALARM, "Clearing for unit testing")
        time.sleep(0.2)

        (status, fvs) = self.eventStateTbl.get("state")
        for fv in fvs:
            if fv[0] == "cleared":
                newClearCount = int(fv[1])

        (status, fvs) = self.alarmStateTbl.get("state")
        for fv in fvs:
            if fv[0] == "alarms":
                newAlarmCount = int(fv[1])
            if fv[0] == "warning":
                newWarningCount = int(fv[1])

        if (clearCount+1) == newClearCount:
            if (alarmCount-1) == newAlarmCount:
                if (warningCount-1) == newWarningCount:
                    print("test_clear_alarm success")
                else:
                    print("ERROR: test_clear_alarm  severity count failed" + " " + str(warningCount) + " " + str(newWarningCount))
            else:
                print("ERROR: test_clear_alarm  alarm count failed" + " " + str(alarmCount) + " " + str(newAlarmCount))
        else:
            print("ERROR: test_clear_alarm failed" + " " + str(clearCount) + " " + str(newClearCount))

    def ack_alarm(self):
        print("\nTEST: ack alarm")
        (status, fvs) = self.eventStateTbl.get("state")
        ackCount = 0
        newAckCount = 0

        for fv in fvs:
            if fv[0] == "acked":
                ackCount = int(fv[1])

        (status, fvs) = self.alarmStateTbl.get("state")
        for fv in fvs:
            if fv[0] == "acknowledged":
                alarmAckCount = int(fv[1])

        self.notify.logevent("DUMMY_ALARM", "test_ack_alarm", eventnotify.EvAction.RAISE_ALARM, "RAISing for unit testing")
        time.sleep(0.2)

        alm_keys = self.alarmTbl.getKeys()
        print(alm_keys)
        for key in alm_keys:
            (status, fvs) = self.alarmTbl.get(key)
            for fv in fvs:
                if fv[1] == "test_ack_alarm":
                    raise_id = key

        print("raise_id is " + raise_id)
        self.notify.logevent("", raise_id, eventnotify.EvAction.ACK_ALARM, "ACKNOWLEDGing for unit testing")
        time.sleep(0.2)

        (status, fvs) = self.eventStateTbl.get("state")
        for fv in fvs:
            if fv[0] == "acked":
                newAckCount = int(fv[1])

        (status, fvs) = self.alarmStateTbl.get("state")
        ackTime = ""
        for fv in fvs:
            if fv[0] == "acknowledged":
                newAlarmAckCount = int(fv[1])
            if fv[0] == "acknowledge-time":
                ackTime = fv[1]

        if (ackCount+1) == newAckCount:
            if (alarmAckCount+1) == newAlarmAckCount:
                if not ackTime:
                    print("test_ack_alarm success")
                else:
                    print("ERROR: test_ack_alarm acknowedge-time not populated")
            else:
                print("ERROR: test_ack_alarm  alarm-stats ack count failed" + " " + str(alarmAckCount) + " " + str(newAlarmAckCount))
        else:
            print("ERROR: test_ack_alarm event-stats ack count failed" + " " + str(ackCount) + " " + str(newAckCount))

        self.notify.logevent("DUMMY_ALARM", "test_ack_alarm", eventnotify.EvAction.CLEAR_ALARM, "CLEARing for unit testing")

    def unack_alarm(self):
        print("\nTEST: unack alarm")

        self.notify.logevent("DUMMY_ALARM", "test_unack_alarm", eventnotify.EvAction.RAISE_ALARM, "RAISing for unit testing")
        time.sleep(0.2)

        alm_keys = self.alarmTbl.getKeys()
        print(alm_keys)
        for key in alm_keys:
            (status, fvs) = self.alarmTbl.get(key)
            for fv in fvs:
                if fv[1] == "test_unack_alarm":
                    raise_id = key

        print("raise_id is " + raise_id)
        self.notify.logevent("", raise_id, eventnotify.EvAction.ACK_ALARM, "ACKNOWLEDGing for unit testing")
        time.sleep(0.2)

        (status, fvs) = self.alarmStateTbl.get("state")
        for fv in fvs:
            if fv[0] == "acknowledged":
                alarmAckCount = int(fv[1])

        self.notify.logevent("", raise_id, eventnotify.EvAction.UNACK_ALARM, "UNACKNOWLEDGing for unit testing")
        time.sleep(0.2)

        (status, fvs) = self.alarmStateTbl.get("state")
        ackTime = ""
        for fv in fvs:
            if fv[0] == "acknowledged":
                newAlarmAckCount = int(fv[1])
            if fv[0] == "acknowledge-time":
                ackTime = fv[1]

        if (alarmAckCount-1) == newAlarmAckCount:
            if not ackTime:
                print("test_unack_alarm success")
            else:
                print("ERROR: test_unack_alarm acknowedge-time not populated")
        else:
            print("ERROR: test_unack_alarm  alarm-stats ack count failed" + " " + str(alarmAckCount) + " " + str(newAlarmAckCount))

        self.notify.logevent("DUMMY_ALARM", "test_unack_alarm", eventnotify.EvAction.CLEAR_ALARM, "CLEARing for unit testing")

    def evprofile_change_alarm_severity(self):
        data = {}
        data['events'] = []
        data['events'].append({
            'name': 'DUMMY_ALARM',
            'severity': 'CRITICAL',
            'enable': 'true'
        })

        with open('unittest.json', 'w') as outfile:
            json.dump(data, outfile)

    def evprofile_disable_event(self):
        pass

ut = EventUnitTest()
ut.unittest_init()
ut.test_event()
ut.raise_alarm()
ut.clear_alarm()
ut.ack_alarm()
ut.unack_alarm()

