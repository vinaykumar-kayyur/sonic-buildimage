/*
 * MuxManagerTest.h
 *
 *  Created on: Jun 4, 2021
 *      Author: taahme
 */

#ifndef MUXMANAGERTEST_H_
#define MUXMANAGERTEST_H_

#include <memory>
#include <tuple>
#include "gtest/gtest.h"

#include "FakeDbInterface.h"
#include "NetMsgInterface.h"

namespace mux {
class MuxManager;
}

namespace test
{

class MuxManagerTest: public testing::Test
{
public:
    MuxManagerTest();
    virtual ~MuxManagerTest() = default;

    void runIoService(uint32_t count = 1);
    common::MuxPortConfig::Mode getMode(std::string port);
    uint32_t getPositiveStateChangeRetryCount(std::string port);
    uint32_t getNegativeStateChangeRetryCount(std::string port);
    uint32_t getTimeoutIpv4_msec(std::string port);
    uint32_t getTimeoutIpv6_msec(std::string port);
    uint32_t getLinkWaitTimeout_msec(std::string port);
    boost::asio::ip::address getBladeIpv4Address(std::string port);
    boost::asio::ip::address getLoopbackIpv4Address(std::string port);
    void processMuxPortConfigNotifiction(std::deque<swss::KeyOpFieldsValuesTuple> &entries);
    void processServerIpAddress(std::vector<swss::KeyOpFieldsValuesTuple> &servers);
    void processLoopback2InterfaceInfo(std::vector<std::string> &loopbackIntfs);
    void processMuxResponseNotifiction(std::deque<swss::KeyOpFieldsValuesTuple> &entries);
    void processMuxLinkmgrConfigNotifiction(std::deque<swss::KeyOpFieldsValuesTuple> &entries);
    void createPort();

public:
    std::shared_ptr<mux::MuxManager> mMuxManagerPtr;
    std::shared_ptr<FakeDbInterface> mDbInterfacePtr;
    mux::NetMsgInterface mNetMsgInterface;
};

class MuxConfigUpdateTest: public MuxManagerTest,
                           public testing::WithParamInterface<std::tuple<std::string, common::MuxPortConfig::Mode>>
{
};

} /* namespace test */

#endif /* MUXMANAGERTEST_H_ */
