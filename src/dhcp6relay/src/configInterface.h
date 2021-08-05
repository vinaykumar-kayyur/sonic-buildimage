#include <boost/thread.hpp>
#include "subscriberstatetable.h"
#include "select.h"
#include "relay.h"

void initialize_swss(std::vector<arg_config> *vlans);

void deinitialize_swss();

void handleSwssNotification(std::vector<arg_config> *vlans);

void handleRelayNotification(swss::SubscriberStateTable &configMuxTable, std::vector<arg_config> *vlans);

void processRelayNotification(std::deque<swss::KeyOpFieldsValuesTuple> &entries, std::vector<arg_config> *vlans);

void stopSwssNotificationPoll();
