#include "eventconsume.h"
#include "eventnotify.h"
#include "dbconnector.h"
#include "subscriberstatetable.h"
#include "select.h"
#include "loghandler.h"
#include "eventutils.h"
#include <string.h>
#include <math.h>
#include <mutex>
#include <syslog.h>
#include <dlfcn.h>
#include <limits.h>
#include <queue>
#include <cstdlib>
#include <iostream>
#include <fstream>
#include <sstream>
#include <unistd.h>
#include <algorithm>
#include <string>

namespace evt {

using namespace swss;
using namespace std;
using namespace evtutils;
using namespace std::chrono;

constexpr size_t LOG_SZ           = 500;
constexpr char LOG_TYPE_EVENT[]   = "event";
constexpr char LOG_TYPE_ALARM[]   = "alarm";

// map to store sequence-id for alarms
unordered_map<string, uint64_t> cal_lookup_map;

// Map to hold "default" map of events
EventMap default_static_event_table;

// temporary map to hold merge of default map of events and any event profile
EventMap static_event_table;

volatile bool g_run = true;
uint64_t seq_id = 0;
uint64_t PURGE_SECONDS = 86400;

//typedef pair<uint64_t, uint64_t> pi;
typedef pair<uint64_t, uint64_t> pi;
priority_queue<pi, vector<pi>, greater<pi> > event_history_list;

map<string, int> SYSLOG_SEVERITY = {
    {EVENT_SEVERITY_CRITICAL_STR,      LOG_ALERT},
    {EVENT_SEVERITY_MAJOR_STR,         LOG_CRIT},
    {EVENT_SEVERITY_MINOR_STR,         LOG_ERR},
    {EVENT_SEVERITY_WARNING_STR,       LOG_WARNING},
    {EVENT_SEVERITY_INFORMATIONAL_STR, LOG_NOTICE}
};

map <int, string> SYSLOG_SEVERITY_STR = {
    {LOG_ALERT   , EVENT_SEVERITY_CRITICAL_STR},
    {LOG_CRIT    , EVENT_SEVERITY_MAJOR_STR},
    {LOG_ERR     , EVENT_SEVERITY_MINOR_STR},
    {LOG_WARNING , EVENT_SEVERITY_WARNING_STR},
    {LOG_NOTICE  , EVENT_SEVERITY_INFORMATIONAL_STR}
};

static string flood_ev_id;
static string flood_ev_action;
static string flood_ev_resource;
static string flood_ev_msg;

EventConsume::EventConsume(DBConnector* dbConn) :
    m_eventTable(dbConn, EVENT_HISTORY_TABLE_NAME),
    m_alarmTable(dbConn, EVENT_CURRENT_ALARM_TABLE_NAME),
    m_eventStatsTable(dbConn, EVENT_STATS_TABLE_NAME),
    m_alarmStatsTable(dbConn, EVENT_ALARM_STATS_TABLE_NAME),
    m_consumerTable(dbConn, EVENT_PUBSUB_TABLE_NAME),
    m_evprofileTable(dbConn, EVENT_EVPROFILE_TABLE_NAME),
    m_eventPubSubTable(dbConn, EVENT_PUBSUB_TABLE_NAME) {
    SWSS_LOG_ENTER();

    // open syslog connection
    openSyslog();

    // init stats
    initStats();

    // populate local queue of event history table
    read_events();

    // read and apply eventd configuration files 
    // read eventd.json and apply it on history table. 
    // read default and custom profiles, build static_event_table
    read_eventd_config();

    // if symlink pointing to default/custom profile, doesnt exist, create one
    create_symlink();

    SWSS_LOG_NOTICE("DONE WITH EventConsume constructor");
}

EventConsume::~EventConsume() {
}

uint64_t EventConsume::get_seq_id() {
   return seq_id;
}

void EventConsume::run()
{
    SWSS_LOG_ENTER();

    swss::Select s;
    KeyOpFieldsValuesTuple kco;

    // selectable for various tables
    s.addSelectable(&m_consumerTable);
    s.addSelectable(&m_evprofileTable);

    while (g_run) {
        swss::Selectable *sel;

        std::deque<KeyOpFieldsValuesTuple> kco;

        int result = s.select(&sel);

        if (result == Select::OBJECT) {
            if (sel == &m_evprofileTable) {
                m_evprofileTable.pops(kco);
                handle_custom_evprofile(kco);
            } else if (sel == &m_consumerTable) {
                m_consumerTable.pops(kco);
                handle_notification(kco);
            } else {
                SWSS_LOG_DEBUG("received invalid trigger by select");
            }
        }
    }
}

void EventConsume::read_eventd_config(bool read_all) {
    // read manifest file for config options
    if (read_all) {
        read_config_and_purge();
    }

    // read from default map
    static_event_table.clear();
    if (!parse(EVENTD_DEFAULT_MAP_FILE, static_event_table)) {
        SWSS_LOG_ERROR("Can not initialize event map");
        closeSyslog();
        exit(0);
    }

    // Maintain the native default profile in default_static_event_table.
    if (default_static_event_table.empty()) {
        default_static_event_table = static_event_table;
    }

    // read from any potential event profile
    EventMap profile_map;
    profile_map.clear();
    if (parse(EVENTD_PROFILE_SYMLINK, profile_map)) {
        // merge both default map and profile map
        merge(static_event_table, profile_map);
    }

    SWSS_LOG_NOTICE("Event map is built as follows:");
    for (auto& x: static_event_table) {
        SWSS_LOG_NOTICE("    %s (%s %s %s)", x.first.c_str(), x.second.severity.c_str(), x.second.enable.c_str(), x.second.static_event_msg.c_str());
    }
}

void EventConsume::handle_notification(std::deque<KeyOpFieldsValuesTuple> kco)
{
    SWSS_LOG_ENTER();

    for (auto entry: kco) {
        string ev_id, ev_msg, ev_src, ev_act, ev_timestamp, ev_type("EVENT"), ev_static_msg(""), ev_reckey;
        string ev_sev = string(EVENT_SEVERITY_INFORMATIONAL_STR);
        bool is_raise = false;
        bool is_clear = false;
        bool is_ack = false;
        vector<FieldValueTuple> vec;

	ev_reckey = kfvKey(entry);
        std::string op = kfvOp(entry);
        if (op != "SET") {
            continue;
        }

        // parse the record and fetch various event fields
        const vector<FieldValueTuple>& data = kfvFieldsValues(entry);
        fetchFieldValues(data, vec, ev_id, ev_msg, ev_src, ev_act, ev_timestamp);
        
        // delete the pubsub entry
	m_eventPubSubTable.del(ev_reckey);

        // flood protection. If a rogue application sends same event repeatedly, throttle repeated instances of that event
        if (isFloodedEvent(ev_src, ev_act, ev_id, ev_msg)) {
            continue;
        }

        // get static info
        if (!staticInfoExists(ev_id, ev_act, ev_sev, ev_static_msg, vec)) {
            continue;
        }

        // increment save seq-id for the newly received event
        seq_id++;
        FieldValueTuple seqfv("id", to_string(seq_id));
        vec.push_back(seqfv);

        if (ev_act.length() > 0) {
            SWSS_LOG_DEBUG("ev_act %s", ev_act.c_str());
            ev_type = "ALARM";
            string almkey = ev_id;
            if (!ev_src.empty()) { 
                almkey += "|" + ev_src;
            }

            if (ev_act.compare(EVENT_ACTION_RAISE_STR) == 0) {
                is_raise = true;
		// add entry to the lookup map
                cal_lookup_map.insert(make_pair(almkey, seq_id));

                // add acknowledged field intializing it to false
                FieldValueTuple seqfv1("acknowledged", "false");
                vec.push_back(seqfv1);
                m_alarmTable.set(to_string(seq_id), vec);

                // update alarm counters
                updateAlarmStatistics(ev_sev, ev_act);
            } else if (ev_act.compare(EVENT_ACTION_CLEAR_STR) == 0) {
                is_clear = true;
                SWSS_LOG_DEBUG(" Received clear alarm for %s", almkey.c_str());

                bool ack_flag = false;
                // remove entry from local cache, alarm table
                if (! udpateLocalCacheAndAlarmTable(almkey, ack_flag)) {
                    continue;
                }

                // update alarm counters ONLY if it has not been ack'd before. 
                // This is because when alarm is ack'd, alarms/severity counter is reduced already.
                if (!ack_flag) {
                    updateAlarmStatistics(ev_sev, ev_act);
                } else {
		    // if it has been ack'd before, ack counter would have been incremented for this alrm. 
                    // Now is the time reduce it.
	            clearAckAlarmStatistic();
		}
            } else {
                // ack/unack events comes with seq-id of raised alarm as resource field.
                // fetch details of "raised" alarm record
                string raise_act;
                string raise_ack_flag;
                string raise_ts;

                // fetch information from raised event record
                fetchRaiseInfo(vec, ev_src, ev_id, ev_sev, raise_act, raise_ack_flag, raise_ts);

                if (ev_act.compare(EVENT_ACTION_ACK_STR) == 0) {
                    if (raise_ack_flag.compare("true") == 0) {
                        SWSS_LOG_NOTICE(" %s/%s is already acknowledged", ev_id.c_str(), ev_src.c_str());
                        continue;
                    }
                    if (raise_act.compare(EVENT_ACTION_RAISE_STR) == 0) {
                        is_ack = true;
                        SWSS_LOG_DEBUG(" received ACKnowledge event - %s/%s", ev_id.c_str(), ev_src.c_str());
                        
                        // update the record with ack flag and ack-time and stats
                        updateAckInfo(is_ack, ev_timestamp, ev_sev, ev_act, ev_src);
                    } else {
                        SWSS_LOG_NOTICE(" %s/%s is not in raised state", ev_id.c_str(), ev_src.c_str());
                        continue;
                    }
                } else if (ev_act.compare(EVENT_ACTION_UNACK_STR) == 0) {
                    if (raise_ack_flag.compare("true") == 0) {
                        SWSS_LOG_DEBUG(" received un-ACKnowledge event - %s/%s", ev_id.c_str(), ev_src.c_str());

                        // update the record with ack flag and ack-time and stats
                        updateAckInfo(is_ack, ev_timestamp, ev_sev, ev_act, ev_src);
                    } else {
                        SWSS_LOG_NOTICE(" %s/%s is already un-acknowledged", ev_id.c_str(), ev_src.c_str());
                        continue;
                    }
                }
            }
        }
        // verify the size of history table; delete older entry; add new entry
        update_events(to_string(seq_id), ev_timestamp, vec);

        updateEventStatistics(true, is_raise, is_ack, is_clear);

        // raise a syslog message
        writeToSyslog(ev_id, (int) (SYSLOG_SEVERITY.find(ev_sev)->second), ev_type, ev_act, ev_msg, ev_static_msg);
    }

    return;
}

void EventConsume::read_events() {
    vector<KeyOpFieldsValuesTuple> tuples;
    m_eventTable.getContent(tuples);

    SWSS_LOG_ENTER();
    // find out last sequence-id; build local history list
    for (auto tuple: tuples) {
        for (auto fv: kfvFieldsValues(tuple)) {
            if (fvField(fv) == "time-created") {
                char* end;
                uint64_t seq = strtoull(kfvKey(tuple).c_str(), &end,10);
                if (seq > seq_id) {
                    seq_id = seq;
                }
                uint64_t val = strtoull(fvValue(fv).c_str(), &end,10);
                event_history_list.push(make_pair( seq, val ));
            }
        }
    }
    SWSS_LOG_NOTICE("eventd sequence-id intialized to %lu", seq_id);
}

void EventConsume::updateAlarmStatistics(string ev_sev, string ev_act) {
    vector<FieldValueTuple> vec;
    vector<FieldValueTuple> temp;

    // severity counter names are of lower case
    transform(ev_sev.begin(), ev_sev.end(), ev_sev.begin(), ::tolower);

    if (m_alarmStatsTable.get("state", vec)) {
        for (auto fv: vec) {
            if (!fv.first.compare("alarms")) {
                if ((ev_act.compare(EVENT_ACTION_RAISE_STR) == 0) || (ev_act.compare(EVENT_ACTION_UNACK_STR) == 0)) {
                    fv.second = to_string(stoi(fv.second.c_str())+1);
                } else {
                    fv.second = to_string(stoi(fv.second.c_str())-1);
                }
                temp.push_back(fv);
            } else if (!fv.first.compare(ev_sev)) {
                if ((ev_act.compare(EVENT_ACTION_RAISE_STR) == 0) || (ev_act.compare(EVENT_ACTION_UNACK_STR) == 0)) {
                    fv.second = to_string(stoi(fv.second.c_str())+1);
                } else {
                    fv.second = to_string(stoi(fv.second.c_str())-1);
                }
                temp.push_back(fv);
            } else if (!fv.first.compare("acknowledged")) {
                if (ev_act.compare(EVENT_ACTION_ACK_STR) == 0)  {
                    fv.second = to_string(stoi(fv.second.c_str())+1);
                } else if (ev_act.compare(EVENT_ACTION_UNACK_STR) == 0) { 
                    fv.second = to_string(stoi(fv.second.c_str())-1);
                }
                temp.push_back(fv);
            }
        }
        m_alarmStatsTable.set("state", temp);
    } else {
        SWSS_LOG_ERROR("Can not update alarm statistics (table does not exist)");
    }
}

void EventConsume::updateEventStatistics(bool is_add, bool is_raise, bool is_ack, bool is_clear) {
    vector<FieldValueTuple> vec;
    vector<FieldValueTuple> temp;

    if (m_eventStatsTable.get("state", vec)) {
        for (auto fv: vec) {
            if (!fv.first.compare("events")) {
                if (is_add) {
                    fv.second = to_string(stoi(fv.second.c_str())+1);
                } else {
                    fv.second = to_string(stoi(fv.second.c_str())-1);
                }
                temp.push_back(fv);
            } else if (!fv.first.compare("raised")) {
                if (is_raise) {
                    if (is_add) {
                        fv.second = to_string(stoi(fv.second.c_str())+1);
                    } else {
                        fv.second = to_string(stoi(fv.second.c_str())-1);
                    }
                    temp.push_back(fv);
                }
            } else if (!fv.first.compare("cleared")) {
                if (is_clear) {
                    if (is_add) {
                        fv.second = to_string(stoi(fv.second.c_str())+1);
                    } else {
                        fv.second = to_string(stoi(fv.second.c_str())-1);
                    }
                    temp.push_back(fv);
                }
            } else if (!fv.first.compare("acked")) {
                if (is_ack) {
                    if (is_add) {
                        fv.second = to_string(stoi(fv.second.c_str())+1);
                    } else {
                        fv.second = to_string(stoi(fv.second.c_str())-1);
                    }
                    temp.push_back(fv);
                }
            }
        }

        m_eventStatsTable.set("state", temp);
    } else {
        SWSS_LOG_ERROR("Can not update event statistics (table does not exist)");
    }
}

void EventConsume::modifyEventStats(string seq_id) { 
    vector<FieldValueTuple> rec;
    m_eventTable.get(seq_id, rec);
    bool is_raise = false;
    bool is_clear = false;
    bool is_ack = false;
    for (auto fvr: rec) {
        if (!fvr.first.compare("action")) {
            if (!fvr.second.compare(EVENT_ACTION_RAISE_STR)) {
                is_raise = true;
            } else if (!fvr.second.compare(EVENT_ACTION_CLEAR_STR)) {
                is_clear = true;
            }
        }
        if (!fvr.first.compare("acknowledged")) {
            if (!fvr.second.compare("true")) {
                is_ack = true;
            }
        }
    }
    updateEventStatistics(false, is_raise, is_ack, is_clear);
}

void EventConsume::purge_events() {
    SWSS_LOG_ENTER();
    uint32_t size = event_history_list.size();

    while (size >= count) {
        pair <uint64_t,uint64_t> oldest_entry = event_history_list.top();
        SWSS_LOG_NOTICE("Rollover based on count(%d/%d). Deleting %lu", size, count, oldest_entry.first);
        m_eventTable.del(to_string(oldest_entry.first));
        modifyEventStats(to_string(oldest_entry.first));
        event_history_list.pop();
        --size;
    }

    const auto p1 = system_clock::now();
    unsigned tnow_seconds = duration_cast<seconds>(p1.time_since_epoch()).count();

    while (!event_history_list.empty()) {
        pair <uint64_t,uint64_t> oldest_entry = event_history_list.top();
	unsigned old_seconds = oldest_entry.second / 1000000000ULL;

        if ((tnow_seconds - old_seconds) > PURGE_SECONDS) {
            SWSS_LOG_NOTICE("Rollover based on time (%lu days). Deleting %lu.. now %u old %u", (PURGE_SECONDS/days), oldest_entry.first, tnow_seconds, old_seconds);
            m_eventTable.del(to_string(oldest_entry.first));
            modifyEventStats(to_string(oldest_entry.first));
            event_history_list.pop();
        } else {
            return;
        }
    }
    return;
}

void EventConsume::read_config_and_purge() {
    days = 0;
    count = 0;
    // read from the manifest file
    parse_config(EVENTD_CONF_FILE, days, count);
    SWSS_LOG_NOTICE("max-days %d max-records %d", days, count);

    // update the nanosecond limit
    PURGE_SECONDS *= days; 

    // purge events based on # of days
    purge_events();
}

void EventConsume::update_events(string seq_id, string ts, vector<FieldValueTuple> vec) {
    // purge events based on # of days
    purge_events();

    // now add the event to the event table
    m_eventTable.set(seq_id, vec);

    // store it into the event history list
    char* end;
    uint64_t seq = strtoull(seq_id.c_str(), &end, 10);
    uint64_t val = strtoull(ts.c_str(), &end, 10);
    event_history_list.push(make_pair( seq, val ));
}

void EventConsume::handle_custom_evprofile(std::deque<KeyOpFieldsValuesTuple> entries) {
    string filename;
    for (auto entry: entries) {
        std::string op = kfvOp(entry);
        if (op != "SET") return;
        const vector<FieldValueTuple>& data = kfvFieldsValues(entry);
        for (auto idx : data) {
            if (fvField(idx) == "name") {
                filename = fvValue(idx);
                break;
            }
        }
    }

    if (filename.empty()) {
        SWSS_LOG_ERROR("Received Event Profile name is empty.");
        return;
    }
    string custom_profile = EVENTD_PROFILE_DIR + filename;

    SWSS_LOG_DEBUG("Received profile is %s", custom_profile.c_str());
    
    // make sure that event profile is not already configured
    char buf[1024];
    std::size_t len;
    if ((len = readlink(EVENTD_PROFILE_SYMLINK, buf, sizeof(buf)-1)) > 0) {
        buf[len] = '\0';

        if (string(buf).compare(custom_profile) == 0) {
            SWSS_LOG_DEBUG("Event Profile name is already configured.");
            return;
        }
    }

    // the profile is already validated by rest-server. create symlink
    if (unlink(EVENTD_PROFILE_SYMLINK) != 0) {
        // it is possible.. if there is no symlink exists and user trying for the first time
        SWSS_LOG_DEBUG("Unlink of custom profile failed");
    }
    if (symlink(custom_profile.c_str(), EVENTD_PROFILE_SYMLINK) != 0) {
        SWSS_LOG_ERROR("Error applying custom profile");
    } else {
        SWSS_LOG_DEBUG("Applying custom profile");
        read_eventd_config(false);
        // generate an event informing new profile is in effect
        LOG_EVENT(CUSTOM_EVPROFILE_CHANGE, custom_profile.c_str(), NOTIFY, "Custom Event Profile %s is applied.", filename.c_str());

        // walk through event table and remove those alarms for which enable flag is set to false
        for (auto it : cal_lookup_map) {
            //key in the cal_lookup_map is tokenized with | with event-id and source
            char *evid = strtok((char *) (it.first.c_str()), "|");
            // find the record in the static_event_table that merged the custom profile
            auto itr = static_event_table.find(string(evid));
            if (itr != static_event_table.end()) {
                EventInfo tmp = (EventInfo) (itr->second);
                // if enable flag is false, remove the record from alarm table
                if (tmp.enable == EVENT_ENABLE_FALSE_STR) {
                    SWSS_LOG_NOTICE("enable for evid %s is false.. clearing alarm", evid);
                    uint64_t lookup_seq_id = (long unsigned int) (it.second);
                    cal_lookup_map.erase(it.first);
                    m_alarmTable.del(to_string(lookup_seq_id));                    
                    // update alarm stats
                    updateAlarmStatistics(tmp.severity, EVENT_ACTION_CLEAR_STR);
                }
            }
        }
    }
}

void EventConsume::resetAlarmStats(int alarms, int critical, int major, int minor, int warning, int acknowledged) {
    vector<FieldValueTuple> temp;
    FieldValueTuple fv;
    map<int, string>::iterator it;
    for (it = SYSLOG_SEVERITY_STR.begin(); it != SYSLOG_SEVERITY_STR.end(); it++) {
        // there wont be any informational alarms
        if (it->second.compare(EVENT_SEVERITY_CRITICAL_STR) == 0) {
            fv = FieldValueTuple("critical", to_string(critical));
            temp.push_back(fv);
        } else if (it->second.compare(EVENT_SEVERITY_MAJOR_STR) == 0) {
            fv = FieldValueTuple("major", to_string(major));
            temp.push_back(fv);
        } else if (it->second.compare(EVENT_SEVERITY_MINOR_STR) == 0) {
            fv = FieldValueTuple("minor", to_string(minor));
            temp.push_back(fv);
        } else if (it->second.compare(EVENT_SEVERITY_WARNING_STR) == 0) {
            fv = FieldValueTuple("warning", to_string(warning));
            temp.push_back(fv);
        }
    }
    fv = FieldValueTuple("alarms", to_string(alarms));
    temp.push_back(fv);
    fv = FieldValueTuple("acknowledged", to_string(acknowledged));
    temp.push_back(fv);
    m_alarmStatsTable.set("state", temp);
}

void EventConsume::clearAckAlarmStatistic() {
    vector<FieldValueTuple> vec;
    vector<FieldValueTuple> temp;

    if (m_alarmStatsTable.get("state", vec)) {
        for (auto fv: vec) {
            if (!fv.first.compare("acknowledged")) {
                fv.second = to_string(stoi(fv.second.c_str())-1);
                temp.push_back(fv);
                m_alarmStatsTable.set("state", temp);
		return;
            }
        }
    } 
}


void EventConsume::fetchFieldValues(const vector<FieldValueTuple>& data, 
                                    vector<FieldValueTuple> &vec, 
                                    string &ev_id, 
                                    string &ev_msg, 
                                    string &ev_src, 
                                    string &ev_act, 
                                    string &ev_timestamp) {
    for (auto idx : data) {
        if (fvField(idx) == "type-id") {
            ev_id = fvValue(idx);
            vec.push_back(idx);
            SWSS_LOG_DEBUG("type-id: <%s> ", ev_id.c_str());
        } else if (fvField(idx) == "text") {
            ev_msg = fvValue(idx);
            vec.push_back(idx);
            SWSS_LOG_DEBUG("text: <%s> ", ev_msg.c_str());
        } else if (fvField(idx) == "resource") {
            ev_src = fvValue(idx);
            vec.push_back(idx);
            SWSS_LOG_DEBUG("resource: <%s> ", ev_src.c_str());
        } else if (fvField(idx) == "action") {
            ev_act = fvValue(idx);
            // for events, action is empty
            if (!ev_act.empty()) {
                vec.push_back(idx);
            }
        } else if (fvField(idx) == "time-created") {
            ev_timestamp = fvValue(idx);
            vec.push_back(idx);
            SWSS_LOG_DEBUG("time-created: <%s> ", ev_timestamp.c_str());
        }
    }
}

bool EventConsume::isFloodedEvent(string ev_src, string ev_act, string ev_id, string ev_msg) {
    // flood protection. If a rogue application sends same event repeatedly, throttle repeated instances of that event
    if (!flood_ev_resource.compare(ev_src) &&
        !flood_ev_action.compare(ev_act) &&
        !flood_ev_id.compare(ev_id) &&
        !(flood_ev_msg.compare(ev_msg))) {
            SWSS_LOG_INFO("Ignoring the event %s from %s action %s msg %s as it is repeated", ev_id.c_str(), ev_src.c_str(), ev_act.c_str(), ev_msg.c_str());
            return true;
    }

    flood_ev_resource = ev_src;
    flood_ev_action = ev_act;
    flood_ev_id = ev_id;
    flood_ev_msg = ev_msg;
    return false;
}

bool EventConsume::staticInfoExists(string &ev_id, string &ev_act, string &ev_sev, string &ev_static_msg, vector<FieldValueTuple> &vec) {
    auto it = static_event_table.find(ev_id);
    if (it != static_event_table.end()) {
        EventInfo tmp = (EventInfo) (it->second);
        // discard the event as event_static_map shows enable is false for this event
        if (tmp.enable == EVENT_ENABLE_FALSE_STR) {
            SWSS_LOG_INFO("Discarding event <%s> as it is set to disabled", ev_id.c_str());
            return false;;
        }

        // get severity in the map and store it in the db
        ev_sev = tmp.severity;
        ev_static_msg = tmp.static_event_msg;
        SWSS_LOG_DEBUG("static info: <%s> <%s> ", tmp.severity.c_str(), tmp.static_event_msg.c_str());

        FieldValueTuple seqfv1("severity", tmp.severity);
        vec.push_back(seqfv1);
        return true;
    } else {
        // dont process the incoming alarms if action is neither raise nor clear
        // for ack/unack, no need for this check
        if ((ev_act.compare(EVENT_ACTION_ACK_STR) && ev_act.compare(EVENT_ACTION_UNACK_STR))) {
            SWSS_LOG_ERROR("static info NOT FOUND for <%s> ", ev_id.c_str());
            return false;
        }
    }
    return true;
}

bool EventConsume::udpateLocalCacheAndAlarmTable(string almkey, bool &ack_flag) {
    // find and remove the raised alarm
    uint64_t lookup_seq_id = 0;
    auto it = cal_lookup_map.find(almkey);
    if (it != cal_lookup_map.end()) {
        lookup_seq_id = (uint64_t) (it->second);
        cal_lookup_map.erase(almkey);

        // get status of is_aknowledged flag so that we dont decrement counters twice
        vector<FieldValueTuple> alm_rec;
        m_alarmTable.get(to_string(lookup_seq_id), alm_rec);
        for (auto fvr: alm_rec) {
            if (!fvr.first.compare("acknowledged")) {
                ack_flag = (fvr.second.compare("true") == 0) ? true : false;
                break;
            }
        }

        // delete the record from alarm table
        m_alarmTable.del(to_string(lookup_seq_id));
    } else {
        // possible - when event profile removes alarms for which enable is false and application cleared them later.
        // ignore by logging a debug message..
        SWSS_LOG_INFO("Received alarm-clear for non-existing alarm %s", almkey.c_str());
        return false;
    }
    return true;
}

void EventConsume::initStats() {
    vector<FieldValueTuple> vec;
    // possible after a cold-boot or very first time
    if (! m_eventStatsTable.get("state", vec)) {
        FieldValueTuple fv;
        vector<FieldValueTuple> temp;

        SWSS_LOG_DEBUG("resetting Event Statistics table");
        fv = FieldValueTuple("events", to_string(0));
        temp.push_back(fv);
        fv = FieldValueTuple("raised", to_string(0));
        temp.push_back(fv);
        fv = FieldValueTuple("cleared", to_string(0));
        temp.push_back(fv);
        fv = FieldValueTuple("acked", to_string(0));
        temp.push_back(fv);
        m_eventStatsTable.set("state", temp);
    }
    if (! m_alarmStatsTable.get("state", vec)) {
        SWSS_LOG_DEBUG("resetting Alarm Statistics table");
        resetAlarmStats(0, 0, 0, 0, 0, 0);
    }
}

void EventConsume::updateAckInfo(bool is_ack, string ev_timestamp, string ev_sev, string ev_act, string ev_src) {
    vector<FieldValueTuple> ack_vec;

    FieldValueTuple seqfv1("acknowledged", (is_ack ? "true" : "false"));
    ack_vec.push_back(seqfv1);

    FieldValueTuple seqfv2("acknowledge-time", ev_timestamp);
    ack_vec.push_back(seqfv2);

    // update alarm stats
    updateAlarmStatistics(ev_sev, ev_act);

    // update alarm/event tables for the "raise" record with ack flag and ack timestamp
    // for ack/unack, ev_src contains the "seq-id"
    m_alarmTable.set(ev_src, ack_vec);
    m_eventTable.set(ev_src, ack_vec);
}


void EventConsume::fetchRaiseInfo(vector<FieldValueTuple> &vec, string ev_src, string &ev_id, string &ev_sev, string &raise_act, 
                                  string &raise_ack_flag, string &raise_ts) {
    vector<FieldValueTuple> raise_vec;
    m_alarmTable.get(ev_src, raise_vec);
    for (auto fv: raise_vec) {
        if (!fv.first.compare("type-id")) {
            ev_id = fv.second;
            vec.push_back(fv);
        }
        if (!fv.first.compare("severity")) {
            ev_sev = fv.second;
            vec.push_back(fv);
        }
        if (!fv.first.compare("action")) {
            raise_act = fv.second;
        }
        if (!fv.first.compare("acknowledged")) {
            raise_ack_flag = fv.second;
        }
        if (!fv.first.compare("time-created")) {
            raise_ts = fv.second;
        }
    }
}

};
