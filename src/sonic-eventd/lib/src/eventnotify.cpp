#include "eventnotify.h"
#include <algorithm>
#include <stdarg.h>
#include <stdio.h>
#include <syslog.h>
#include <fstream>
#include <sstream>
#include <iomanip>
#include <stdexcept>
#include <vector>
#include <iostream>
#include <ctime>
#include <ratio>
#include <chrono>
#include "schema.h"
#include "select.h"
#include "dbconnector.h"
#include "redisclient.h"
#include "timestamp.h"

using namespace swss;
using namespace std;
using namespace std::chrono;

namespace alertmgr {

string getActionStr(int action);
string getTimestamp();
EventNotify *EventNotify::m_pInstance = NULL;
uint64_t seq_id = 1;

EventNotify::EventNotify(DBConnector* stateDbConnector): 
    m_statePubsubTable(stateDbConnector, EVENT_PUBSUB_TABLE_NAME) {
    SWSS_LOG_ENTER();
}

EventNotify::~EventNotify() {
}

EventNotify *EventNotify::getInstance()
{
   if (!m_pInstance) {
      DBConnector db("EVENT_DB", 0);
      m_pInstance = new EventNotify(&db);
   }

   return m_pInstance;
}

// timeticks are relative to the Unix Epoch 
string getTimestamp() {
    const auto p1 = system_clock::now();
    return to_string(duration_cast<nanoseconds>(p1.time_since_epoch()).count());
}

string getActionStr(int action) {
    switch (action) {
        case CLEAR_ALARM:
            return string("CLEAR");
        case RAISE_ALARM:
            return string("RAISE");
        case ACK_ALARM:
            return string("ACKNOWLEDGE");
        case UNACK_ALARM:
            return string("UNACKNOWLEDGE");
        default:
            return string();
    }
}

void EventNotify::_send_event(const char *ev_name_p, const char *source_p, int action, const char *fmt, ...)
{
    va_list args;
    char buff[1024];
    memset(buff, 0, sizeof(buff));

    SWSS_LOG_ENTER();

    va_start(args, fmt);
    vsnprintf(buff, sizeof(buff), fmt, args);
    va_end (args);

    string tblkey = string(ev_name_p) + to_string(seq_id++);
    vector<FieldValueTuple> fvs;
    fvs.emplace_back("type-id", string(ev_name_p));
    fvs.emplace_back("text", buff);
    fvs.emplace_back("action", getActionStr(action));
    if (source_p && (strlen(source_p) > 0)) {
        fvs.emplace_back("resource", string(source_p));
    }
    fvs.emplace_back("time-created", getTimestamp());

    m_statePubsubTable.set(tblkey, fvs);
}

};
