#include <boost/thread.hpp>
#include "subscriberstatetable.h"
#include "select.h"
#include "relay.h"

/**
 * @code                void deinitialize_swss()
 * 
 * @brief               initialize DB tables and start SWSS listening thread
 *
 * @return              none
 */
void initialize_swss(std::vector<arg_config> *vlans, swss::DBConnector *db);

/**
 * @code                void deinitialize_swss()
 * 
 * @brief               deinitialize DB interface and join SWSS listening thread
 *
 * @return              none
 */
void deinitialize_swss();

/**
 * @code                void handleSwssNotification(std::vector<arg_config> *vlans)
 * 
 * @brief               main thread for handling SWSS notification
 *
 * @param context       list of vlans/argument config that contains strings of server and option
 *
 * @return              none
 */
void handleSwssNotification(std::vector<arg_config> *vlans);

/**
 * @code                    void handleRelayNotification(swss::SubscriberStateTable &ipHelpersTable, std::vector<arg_config> *vlans)
 * 
 * @brief                   handles DHCPv6 relay configuration change notification
 *
 * @param ipHelpersTable    DHCP table
 * @param context           list of vlans/argument config that contains strings of server and option
 *
 * @return                  none
 */
void handleRelayNotification(swss::SubscriberStateTable &configMuxTable, std::vector<arg_config> *vlans);

/**
 * @code                    void processRelayNotification(std::deque<swss::KeyOpFieldsValuesTuple> &entries, std::vector<arg_config> *vlans)
 * 
 * @brief                   process DHCPv6 relay servers and options configuration change notification
 *
 * @param entries           queue of std::tuple<std::string, std::string, std::vector<FieldValueTuple>> entries in DHCP table
 * @param context           list of vlans/argument config that contains strings of server and option
 *
 * @return                  none
 */
void processRelayNotification(std::deque<swss::KeyOpFieldsValuesTuple> &entries, std::vector<arg_config> *vlans);

/**
*@code      stopSwssNotificationPoll
*
*@brief     stop SWSS listening thread
*
*@return    none
*/
void stopSwssNotificationPoll();
