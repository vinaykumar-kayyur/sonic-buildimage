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

    void runIoService(uint32_t count = 0);
    void postLinkProberEvent(link_prober::LinkProberState::Label label, uint32_t count = 0);
    void postMuxEvent(mux_state::MuxState::Label label);
    void postLinkEvent(link_state::LinkState::Label label);
    void postSuspendTimerExpiredEvent(uint32_t count = 0);
    void handleMuxState(std::string, uint32_t count = 0);
    void handleGetMuxState(std::string);
    void handleProbeMuxState(std::string, uint32_t count = 0);
    void handleLinkState(std::string linkState);
    void handleMuxConfig(std::string config, uint32_t count = 0);
    void activateStateMachine();
    void setMuxActive();
    void setMuxStandby();

public:
    boost::asio::io_service mIoService;
    common::MuxConfig mMuxConfig;
    std::shared_ptr<FakeDbInterface> mDbInterfacePtr;
    std::string mPortName = "EtherTest01";
    std::string mSmartNicIpAddress = "192.168.1.20";
    uint16_t mServerId = 01;

    FakeMuxPort mFakeMuxPort;
    link_manager::LinkManagerStateMachine::CompositeState mTestCompositeState;

    uint8_t mPositiveUpdateCount = 2;
};

} /* namespace test */

#endif /* LINKMANAGERSTATEMACHINETEST_H_ */
