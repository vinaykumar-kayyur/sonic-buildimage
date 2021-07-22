#include <sstream>
#include <syslog.h>
#include <algorithm>
#include "configInterface.h"

constexpr auto DEFAULT_TIMEOUT_MSEC = 1000;

bool mPollSwssNotifcation = true;
std::shared_ptr<boost::thread> mSwssThreadPtr;

//
// ---> initialize();
//
// initialize DB tables and start SWSS listening thread
//
void initialize_swss(arg_config *context)
{
    try {
        mSwssThreadPtr = std::make_shared<boost::thread> (&handleSwssNotification, context);
    }
    catch (const std::bad_alloc &e) {
        syslog(LOG_ERR, "Failed allocate memory. Exception details: %s", e.what());
    }
}

//
// ---> deinitialize();
//
// deinitialize DB interface and join SWSS listening thread
//
void deinitialize_swss()
{
    stopSwssNotificationPoll();
    mSwssThreadPtr->interrupt();
}

/**
 * @code                void handleSwssNotification(arg_config *context)
 * 
 * @brief               main thread for handling SWSS notification
 *
 * @param context       argument config that contains strings of server and option
 *
 * @return              none
 */
void handleSwssNotification(arg_config *context)
{
    std::shared_ptr<swss::DBConnector> configDbPtr = std::make_shared<swss::DBConnector> ("CONFIG_DB", 0);
    swss::SubscriberStateTable ipHelpersTable(configDbPtr.get(), "DHCP");

    swss::Select swssSelect;
    swssSelect.addSelectable(&ipHelpersTable);
    while (mPollSwssNotifcation) {
        swss::Selectable *selectable;
        int ret = swssSelect.select(&selectable, DEFAULT_TIMEOUT_MSEC);
        if (ret == swss::Select::ERROR) {
            syslog(LOG_WARNING, "Select: returned ERROR");
            continue;
        } else if (ret == swss::Select::TIMEOUT) {
            continue;
        } 
        if (selectable == static_cast<swss::Selectable *> (&ipHelpersTable)) {
            handleRelayNotification(ipHelpersTable, context);
        }
    } 
}

/**
 * @code                    void handleRelayNotification(swss::SubscriberStateTable &ipHelpersTable, arg_config context)
 * 
 * @brief                   handles DHCPv6 relay configuration change notification
 *
 * @param ipHelpersTable    DHCP table
 * @param context           argument config that contains strings of server and option
 *
 * @return                  none
 */
void handleRelayNotification(swss::SubscriberStateTable &ipHelpersTable, arg_config *context)
{
    std::deque<swss::KeyOpFieldsValuesTuple> entries;

    ipHelpersTable.pops(entries);
    processRelayNotification(entries, context);
}

/**
 * @code                    void processRelayNotification(std::deque<swss::KeyOpFieldsValuesTuple> &entries, arg_config context)
 * 
 * @brief                   process DHCPv6 relay servers and options configuration change notification
 *
 * @param entries           queue of std::tuple<std::string, std::string, std::vector<FieldValueTuple>> entries in DHCP table
 * @param context           argument config that contains strings of server and option
 *
 * @return                  none
 */
void processRelayNotification(std::deque<swss::KeyOpFieldsValuesTuple> &entries, arg_config *context)
{
    std::vector<std::string> servers;

    for (auto &entry: entries) {
        std::string vlan = kfvKey(entry);
        std::vector<swss::FieldValueTuple> fieldValues = kfvFieldsValues(entry);

        for (auto &fieldValue: fieldValues) {
            std::string f = fvField(fieldValue);
            std::string v = fvValue(fieldValue);
            if(f == "dhcpv6_servers") {
                std::stringstream ss(v);
                while (ss.good()) {
                    std::string substr;
                    getline(ss, substr, ',');
                    context->servers.push_back(substr);
                }
            }
            if(f == "options") {
                std::stringstream ss(v);
                while (ss.good()) {
                    std::string substr;
                    getline(ss, substr, ',');
                    if(substr == "79")
                        context->is_option_79 = true;
                }
            }
        }
    }
}

/**
*@code      stopSwssNotificationPoll
*
*@brief     stop SWSS listening thread
*
*@return    none
*/
void stopSwssNotificationPoll() {
    mPollSwssNotifcation = false;
};
