/*
 * MuxManagerTest.cpp
 *
 *  Created on: Jun 4, 2021
 *      Author: taahme
 */

#include "MuxManagerTest.h"
#include "MuxManager.h"

namespace test
{

MuxManagerTest::MuxManagerTest() :
    mMuxManagerPtr(std::make_shared<mux::MuxManager> ()),
    mDbInterfacePtr(std::make_shared<FakeDbInterface> (mMuxManagerPtr.get(), &mMuxManagerPtr->getIoService())),
    mNetMsgInterface(*mDbInterfacePtr)
{
    mMuxManagerPtr->setDbInterfacePtr(mDbInterfacePtr);

    link_prober::IcmpPayload::generateGuid();
    link_manager::LinkManagerStateMachine::initializeTransitionFunctionTable();
}

void MuxManagerTest::runIoService(uint32_t count)
{
    for (uint32_t i = 0; i < count; i++) {
        mMuxManagerPtr->getIoService().run_one();
        mMuxManagerPtr->getIoService().reset();
    }
}

common::MuxPortConfig::Mode MuxManagerTest::getMode(std::string port)
{
    std::shared_ptr<mux::MuxPort> muxPortPtr = mMuxManagerPtr->mPortMap[port];
    return muxPortPtr->mMuxPortConfig.getMode();
}

uint32_t MuxManagerTest::getPositiveStateChangeRetryCount(std::string port)
{
    std::shared_ptr<mux::MuxPort> muxPortPtr = mMuxManagerPtr->mPortMap[port];
    return muxPortPtr->mMuxPortConfig.getPositiveStateChangeRetryCount();
}

uint32_t MuxManagerTest::getNegativeStateChangeRetryCount(std::string port)
{
    std::shared_ptr<mux::MuxPort> muxPortPtr = mMuxManagerPtr->mPortMap[port];
    return muxPortPtr->mMuxPortConfig.getNegativeStateChangeRetryCount();
}

uint32_t MuxManagerTest::getTimeoutIpv4_msec(std::string port)
{
    std::shared_ptr<mux::MuxPort> muxPortPtr = mMuxManagerPtr->mPortMap[port];
    return muxPortPtr->mMuxPortConfig.getTimeoutIpv4_msec();
}

uint32_t MuxManagerTest::getTimeoutIpv6_msec(std::string port)
{
    std::shared_ptr<mux::MuxPort> muxPortPtr = mMuxManagerPtr->mPortMap[port];
    return muxPortPtr->mMuxPortConfig.getTimeoutIpv6_msec();
}

uint32_t MuxManagerTest::getLinkWaitTimeout_msec(std::string port)
{
    std::shared_ptr<mux::MuxPort> muxPortPtr = mMuxManagerPtr->mPortMap[port];
    return muxPortPtr->mMuxPortConfig.getLinkWaitTimeout_msec();
}

boost::asio::ip::address MuxManagerTest::getBladeIpv4Address(std::string port)
{
    std::shared_ptr<mux::MuxPort> muxPortPtr = mMuxManagerPtr->mPortMap[port];
    return muxPortPtr->mMuxPortConfig.getBladeIpv4Address();
}

boost::asio::ip::address MuxManagerTest::getLoopbackIpv4Address(std::string port)
{
    std::shared_ptr<mux::MuxPort> muxPortPtr = mMuxManagerPtr->mPortMap[port];
    return muxPortPtr->mMuxPortConfig.getLoopbackIpv4Address();
}

void MuxManagerTest::processMuxPortConfigNotifiction(std::deque<swss::KeyOpFieldsValuesTuple> &entries)
{
    mDbInterfacePtr->processMuxPortConfigNotifiction(entries);
}

void MuxManagerTest::processServerIpAddress(std::vector<swss::KeyOpFieldsValuesTuple> &servers)
{
    mDbInterfacePtr->processServerIpAddress(servers);

    EXPECT_TRUE(mMuxManagerPtr->mPortMap.size() == 1);
}

void MuxManagerTest::processLoopback2InterfaceInfo(std::vector<std::string> &loopbackIntfs)
{
    mDbInterfacePtr->processLoopback2InterfaceInfo(loopbackIntfs);
}

void MuxManagerTest::processMuxResponseNotifiction(std::deque<swss::KeyOpFieldsValuesTuple> &entries)
{
    mDbInterfacePtr->processMuxResponseNotifiction(entries);
}

void MuxManagerTest::processMuxLinkmgrConfigNotifiction(std::deque<swss::KeyOpFieldsValuesTuple> &entries)
{
    mDbInterfacePtr->processMuxLinkmgrConfigNotifiction(entries);
}

void MuxManagerTest::createPort()
{
    EXPECT_TRUE(mMuxManagerPtr->mPortMap.size() == 0);

    std::deque<swss::KeyOpFieldsValuesTuple> entries = {
        {"Ethernet0", "SET", {{"oper_status", "up"}}},
    };

    mDbInterfacePtr->processLinkStateNotifiction(entries);
    std::shared_ptr<mux::MuxPort> muxPortPtr = mMuxManagerPtr->mPortMap["Ethernet0"];
    link_manager::LinkManagerStateMachine* linkManagerStateMachine = muxPortPtr->getLinkManagerStateMachine();

    EXPECT_TRUE(mMuxManagerPtr->mPortMap.size() == 1);
    EXPECT_TRUE(linkManagerStateMachine->mComponentInitState.test(link_manager::LinkManagerStateMachine::LinkStateComponent) == 0);

    runIoService();

    EXPECT_TRUE(linkManagerStateMachine->mComponentInitState.test(link_manager::LinkManagerStateMachine::LinkStateComponent) == 1);

    entries.clear();
    entries = {
        {"Ethernet0", "SET", {{"state", "active"}}},
    };

    mDbInterfacePtr->processMuxStateNotifiction(entries);
    EXPECT_TRUE(mMuxManagerPtr->mPortMap.size() == 1);
    EXPECT_TRUE(linkManagerStateMachine->mComponentInitState.test(link_manager::LinkManagerStateMachine::MuxStateComponent) == 0);

    runIoService();

    EXPECT_TRUE(linkManagerStateMachine->mComponentInitState.test(link_manager::LinkManagerStateMachine::MuxStateComponent) == 1);

    // activating the state machine without link prober
    linkManagerStateMachine->mComponentInitState.set(0);
}

TEST_F(MuxManagerTest, AddPort)
{
    createPort();

    std::string ipAddress = "192.168.0.1";
    std::vector<swss::KeyOpFieldsValuesTuple> servers;
    servers = {
        {"Ethernet0", "SET", {{"server_ipv4", ipAddress + "/32"}}},
    };

    processServerIpAddress(servers);
}

TEST_F(MuxManagerTest, Loopback2Address)
{
    createPort();

    std::string ipAddress = "10.10.10.2";
    std::vector<std::string> loopbackIntfs = {
        "Loopback2|2603:10e1:100:d::1/128",
        "Loopback2|" + ipAddress + "/32",
        "Loopback2"
    };

    processLoopback2InterfaceInfo(loopbackIntfs);

    EXPECT_TRUE(getLoopbackIpv4Address("Ethernet0").to_string() == ipAddress);
}

TEST_F(MuxManagerTest, MuxResponse)
{
    std::deque<swss::KeyOpFieldsValuesTuple> entries = {
        {"Ethernet0", "SET", {{"response", "active"}}},
    };
    processMuxResponseNotifiction(entries);
}

TEST_F(MuxManagerTest, LinkmgrdConfig)
{
    createPort();

    uint32_t v4PorbeInterval = 70;
    uint32_t v6ProveInterval = 700;
    uint32_t positiveSignalCount = 2;
    uint32_t negativeSignalCount = 3;
    uint32_t suspendTimer = 5;
    std::deque<swss::KeyOpFieldsValuesTuple> entries = {
        {"LINK_PROBER", "SET", {{"interval_v4", boost::lexical_cast<std::string> (v4PorbeInterval)}}},
        {"LINK_PROBER", "SET", {{"interval_v6", boost::lexical_cast<std::string> (v6ProveInterval)}}},
        {"LINK_PROBER", "SET", {{"positive_signal_count", boost::lexical_cast<std::string> (positiveSignalCount)}}},
        {"LINK_PROBER", "SET", {{"negative_signal_count", boost::lexical_cast<std::string> (negativeSignalCount)}}},
        {"LINK_PROBER", "SET", {{"suspend_timer", boost::lexical_cast<std::string> (suspendTimer)}}},
    };
    processMuxLinkmgrConfigNotifiction(entries);

    EXPECT_TRUE(getTimeoutIpv4_msec("Ethernet0") == v4PorbeInterval);
    EXPECT_TRUE(getTimeoutIpv6_msec("Ethernet0") == v6ProveInterval);
    EXPECT_TRUE(getPositiveStateChangeRetryCount("Ethernet0") == positiveSignalCount);
    EXPECT_TRUE(getNegativeStateChangeRetryCount("Ethernet0") == negativeSignalCount);
    EXPECT_TRUE(getLinkWaitTimeout_msec("Ethernet0") == (negativeSignalCount + 1) * v4PorbeInterval);
}

TEST_P(MuxConfigUpdateTest, MuxPortConfigUpdate)
{
    createPort();

    std::string state = std::get<0> (GetParam());
    std::deque<swss::KeyOpFieldsValuesTuple> entries = {
        {"Ethernet0", "SET", {{"state", state}}},
    };
    processMuxPortConfigNotifiction(entries);
    runIoService();

    EXPECT_TRUE(getMode("Ethernet0") == std::get<1> (GetParam()));
}

INSTANTIATE_TEST_CASE_P(
    AutoActiveManual,
    MuxConfigUpdateTest,
    ::testing::Values(
        std::make_tuple("auto", common::MuxPortConfig::Mode::Auto),
        std::make_tuple("active", common::MuxPortConfig::Mode::Active),
        std::make_tuple("manual", common::MuxPortConfig::Mode::Manual)
    )
);

} /* namespace test */
