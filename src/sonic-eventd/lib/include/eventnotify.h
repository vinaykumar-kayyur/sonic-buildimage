#ifndef SWSS_COMMON_EVENTNOTIFY_H
#define SWSS_COMMON_EVENTNOTIFY_H

#include <string>
#include <chrono>
#include <atomic>
#include <map>
#include <memory>
#include <thread>
#include <mutex>
#include <functional>
#include <ctime>
#include <ratio>
#include <chrono>
#include "dbconnector.h"
#include "table.h"
using namespace swss;
namespace alertmgr {

class EventNotify
{
public:
    static EventNotify *getInstance();
    void _send_event(const char *ev_name_p, const char *source_p, int action, const char *fmt, ...);
private:
    EventNotify() = default;
    ~EventNotify();
    EventNotify(DBConnector* stateDbConnector);
    EventNotify(const EventNotify&);
    static EventNotify *m_pInstance;
    static DBConnector *p_state_db;
    Table m_statePubsubTable;
};

#define NOTIFY       0
#define CLEAR_ALARM  1
#define RAISE_ALARM  2
#define ACK_ALARM    3
#define UNACK_ALARM  4

#define LOG_EVENT(name, source, action, MSG, ...)    alertmgr::EventNotify::getInstance()->_send_event(#name, source, action, MSG, ##__VA_ARGS__)
}

#endif /* SWSS_COMMON_EVENTNOTIFY_H */
