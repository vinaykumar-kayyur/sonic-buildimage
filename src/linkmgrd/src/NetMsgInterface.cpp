/*
 * NetMsgInterface.cpp
 *
 *  Created on: Jan 12, 2021
 *      Author: taahme
 */

#include <array>
#include <string>
#include <netinet/in.h>
#include <netlink/route/link.h>
#include <netlink/route/neighbour.h>

#include "swss/linkcache.h"
#include "swss/macaddress.h"

#include "NetMsgInterface.h"
#include "common/MuxLogger.h"
#include "common/MuxException.h"

#define MAX_ADDR_SIZE   64

namespace mux
{

//
// ---> NetMsgInterface(DbInterface &dbInterface);
//
// class constructor
//
NetMsgInterface::NetMsgInterface(DbInterface &dbInterface) :
    mDbInterface(dbInterface)
{
}

//
// ---> onMsg(int msgType, NetlinkObject *netlinkObject);
//
// handle received net link messages
//
void NetMsgInterface::onMsg(int msgType, NetlinkObject *netlinkObject)
{
    static auto constexpr NONE_MAC = "none";

    if ((msgType == RTM_NEWNEIGH) || (msgType == RTM_GETNEIGH) || (msgType == RTM_DELNEIGH)) {
        RouteNetlinkNeighbor *routeNetlinkNeighbor = reinterpret_cast<RouteNetlinkNeighbor *> (netlinkObject);
        if (rtnl_neigh_get_family(routeNetlinkNeighbor) == AF_INET ||
            rtnl_neigh_get_family(routeNetlinkNeighbor) == AF_INET6) {
            std::string portName = swss::LinkCache::getInstance().ifindexToName(
                rtnl_neigh_get_ifindex(routeNetlinkNeighbor)
            );

            std::array<char, MAX_ADDR_SIZE + 1> macStr;
            nl_addr2str(rtnl_neigh_get_lladdr(routeNetlinkNeighbor), macStr.data(), macStr.size() - 1);

            if (strncmp(macStr.data(), NONE_MAC, strlen(NONE_MAC))) {
                std::array<char, MAX_ADDR_SIZE + 1> ipStr;
                nl_addr2str(rtnl_neigh_get_dst(routeNetlinkNeighbor), ipStr.data(), ipStr.size() - 1);

                MUXLOGDEBUG(boost::format("%s: interface IP '%s', MAC '%s', msgType %d") %
                    portName % ipStr.data() % macStr.data() % msgType
                );

                boost::system::error_code errorCode;

                boost::asio::ip::address ipAddress = boost::asio::ip::make_address(ipStr.data(), errorCode);
                if (!errorCode) {
                    swss::MacAddress macAddress(macStr.data());
                    mDbInterface.updateServerMacAddress(ipAddress, macAddress.getMac());
                }
            }
        }
    }
}

} /* namespace mux */
