#include <boost/thread.hpp>
#include "subscriberstatetable.h"
#include "select.h"
#include "relay.h"

void initialize_swss(arg_config *context);

void deinitialize_swss();

void handleSwssNotification(arg_config *context);

void handleRelayNotification(swss::SubscriberStateTable &configMuxTable, arg_config *context);

void processRelayNotification(std::deque<swss::KeyOpFieldsValuesTuple> &entries, arg_config *context);

void stopSwssNotificationPoll();
