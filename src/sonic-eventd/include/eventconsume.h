#ifndef __EVENTCONSUME_H__
#define __EVENTCONSUME_H__

#include <string>
#include <chrono>
#include <atomic>
#include <map>
#include <memory>
#include <thread>
#include <mutex>
#include <functional>
#include "dbconnector.h"
#include "subscriberstatetable.h"

namespace evt {
using namespace swss;
using namespace std;

class EventConsume
{
public:
    EventConsume(DBConnector* dbConn);
    ~EventConsume();
    void run();
    void read_eventd_config(bool read_all=true);
    uint64_t get_seq_id();

private:
    Table m_eventTable;
    Table m_alarmTable;
    Table m_eventStatsTable;
    Table m_alarmStatsTable;
    SubscriberStateTable m_consumerTable;
    SubscriberStateTable m_evprofileTable;
    Table m_eventPubSubTable;
    u_int32_t days, count;

    void handle_notification(std::deque<KeyOpFieldsValuesTuple> kco);
    void handle_custom_evprofile(std::deque<KeyOpFieldsValuesTuple>);
    void read_events();
    void updateAlarmStatistics(string ev_sev, string ev_act);
    void updateEventStatistics(bool is_add, bool is_alarm, bool is_ack, bool is_clear, bool is_unack);
    void read_config_and_purge();
    void update_events(string seq_id, string ts, vector<FieldValueTuple> vec);
    void purge_events();
    void modifyEventStats(string seq_id);
    void initEventStats(int, int, int, int);
    void initAlarmStats();
    void clearAckAlarmStatistic();
};
}

#endif /* __EVENTCONSUME_H__ */

