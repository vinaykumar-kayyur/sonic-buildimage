/*
 * LinkManagerStateMachineTest.h
 *
 *  Created on: Oct 25, 2020
 *      Author: tamer
 */

#ifndef LINKMANAGERSTATEMACHINETEST_H_
#define LINKMANAGERSTATEMACHINETEST_H_

#include "gtest/gtest.h"

#include "FakeMuxPort.h"
#include "FakeLinkProber.h"

namespace test
{

class LinkManagerStateMachineTest: public ::testing::Test
{
public:
    LinkManagerStateMachineTest();
    virtual ~LinkManagerStateMachineTest() = default;

    virtual void suspendTxProbes();

    void runIoService(uint32_t count = 1);
    void postLinkProberEvent(link_prober::LinkProberState::Label label);
    void postMuxEvent(mux_state::MuxState::Label label);
    void postLinkEvent(link_state::LinkState::Label label);
    void handleMuxState(std::string);
    void handleGetMuxState(std::string);
    void handleProbeMuxState(std::string);
    void handleLinkState(std::string linkState);
    void handleMuxConfig(std::string config);
    void activateStateMachine();
    void setMuxActive();
    void setMuxStandby();

public:
    boost::asio::io_service mIoService;
    common::MuxConfig mMuxConfig;
    FakeDbInterface mDbInterface;
    std::string mPortName = "EtherTest01";
    std::string mSmartNicIpAddress = "192.168.1.20";
    uint16_t mServerId = 01;

    FakeMuxPort mFakeMuxPort;
    link_manager::LinkManagerStateMachine::CompositeState mTestCompositeState;

    uint32_t mSuspendTxProbeCallCount = 0;
};

} /* namespace test */

#endif /* LINKMANAGERSTATEMACHINETEST_H_ */
