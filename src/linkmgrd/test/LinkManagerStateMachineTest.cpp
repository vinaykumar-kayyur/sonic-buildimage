/*
 * LinkManagerStateMachineTest.cpp
 *
 *  Created on: Oct 25, 2020
 *      Author: tamer
 */

#include "LinkManagerStateMachineTest.h"
#include "link_prober/LinkProberStateMachine.h"

#define VALIDATE_STATE(p, m, l) \
    do { \
        mTestCompositeState = mFakeMuxPort.getCompositeState(); \
        EXPECT_EQ(ps(mTestCompositeState), link_prober::LinkProberState::Label::p); \
        EXPECT_EQ(ms(mTestCompositeState), mux_state::MuxState::Label::m); \
        EXPECT_EQ(ls(mTestCompositeState), link_state::LinkState::Label::l); \
    } while (0)

namespace test
{

LinkManagerStateMachineTest::LinkManagerStateMachineTest() :
    mDbInterface(&mIoService),
    mFakeMuxPort(
        &mDbInterface,
        mMuxConfig,
        mPortName,
        mServerId,
        mIoService
    )
{
}

void LinkManagerStateMachineTest::suspendTxProbes()
{
    mSuspendTxProbeCallCount++;
}

void LinkManagerStateMachineTest::runIoService(uint32_t count)
{
    if (count == 0) {
        mIoService.run();
        mIoService.reset();
    }

    for (uint8_t i = 0; i < count; i++) {
        mIoService.run_one();
        mIoService.reset();
    }
}

void LinkManagerStateMachineTest::postLinkProberEvent(link_prober::LinkProberState::Label label, uint32_t count)
{
    for (uint8_t i = 0; i < mMuxConfig.getStateChangeRetryCount(); i++) {
        switch (label) {
        case link_prober::LinkProberState::Active:
            mFakeMuxPort.mFakeLinkProber->postLinkProberEvent<link_prober::IcmpSelfEvent&>(
                link_prober::LinkProberStateMachine::getIcmpSelfEvent()
            );
            break;
        case link_prober::LinkProberState::Standby:
            mFakeMuxPort.mFakeLinkProber->postLinkProberEvent<link_prober::IcmpPeerEvent&>(
                link_prober::LinkProberStateMachine::getIcmpPeerEvent()
            );
            break;
        case link_prober::LinkProberState::Unknown:
            mFakeMuxPort.mFakeLinkProber->postLinkProberEvent<link_prober::IcmpUnknownEvent&>(
                link_prober::LinkProberStateMachine::getIcmpUnknownEvent()
            );
            break;
        default:
            break;
        }
        runIoService(count);
    }
}

void LinkManagerStateMachineTest::postMuxEvent(mux_state::MuxState::Label label)
{
    mux_state::MuxStateMachine& muxStateMachine = mFakeMuxPort.getMuxStateMachine();
    for (uint8_t i = 0; i < mMuxConfig.getMuxStateChangeRetryCount(); i++) {
        switch (label) {
        case mux_state::MuxState::Active:
            muxStateMachine.postMuxStateEvent(mux_state::MuxStateMachine::getActiveEvent());
            break;
        case mux_state::MuxState::Standby:
            muxStateMachine.postMuxStateEvent(mux_state::MuxStateMachine::getStandbyEvent());
            break;
        case mux_state::MuxState::Unknown:
            muxStateMachine.postMuxStateEvent(mux_state::MuxStateMachine::getUnknownEvent());
            break;
        default:
            break;
        }
        runIoService();
    }
}

void LinkManagerStateMachineTest::postLinkEvent(link_state::LinkState::Label label)
{
    link_state::LinkStateMachine& linkStateMachine = mFakeMuxPort.getLinkStateMachine();
    for (uint8_t i = 0; i < mMuxConfig.getLinkStateChangeRetryCount(); i++) {
        switch (label) {
        case link_state::LinkState::Up:
            linkStateMachine.postLinkStateEvent(link_state::LinkStateMachine::getUpEvent());
            break;
        case link_state::LinkState::Down:
            linkStateMachine.postLinkStateEvent(link_state::LinkStateMachine::getDownEvent());
            break;
        default:
            break;
        }
        runIoService();
    }
}

void LinkManagerStateMachineTest::handleMuxState(std::string state, uint32_t count)
{
    mFakeMuxPort.handleMuxState(state);
    runIoService(count);
}

void LinkManagerStateMachineTest::handleGetMuxState(std::string state)
{
    mFakeMuxPort.handleGetMuxState(state);
    runIoService();
}

void LinkManagerStateMachineTest::handleProbeMuxState(std::string state, uint32_t count)
{
    mFakeMuxPort.handleProbeMuxState(state);
    runIoService(count);
}

void LinkManagerStateMachineTest::handleLinkState(std::string linkState)
{
    mFakeMuxPort.handleLinkState(linkState);
    runIoService();
}

void LinkManagerStateMachineTest::handleMuxConfig(std::string config, uint32_t count)
{
    mFakeMuxPort.handleMuxConfig(config);
    runIoService(count);
}

void LinkManagerStateMachineTest::activateStateMachine()
{
    mFakeMuxPort.activateStateMachine();
}

void LinkManagerStateMachineTest::setMuxActive()
{
    activateStateMachine();
    VALIDATE_STATE(Unknown, Wait, Down);

    postLinkEvent(link_state::LinkState::Up);
    VALIDATE_STATE(Wait, Wait, Up);

    // change state to active
    postLinkProberEvent(link_prober::LinkProberState::Active);
    VALIDATE_STATE(Active, Wait, Up);

    // switch mux to active state
    postMuxEvent(mux_state::MuxState::Active);
    VALIDATE_STATE(Active, Active, Up);
}

void LinkManagerStateMachineTest::setMuxStandby()
{
    activateStateMachine();
    VALIDATE_STATE(Unknown, Wait, Down);

    postLinkEvent(link_state::LinkState::Up);
    VALIDATE_STATE(Wait, Wait, Up);

    // change state to active
    postLinkProberEvent(link_prober::LinkProberState::Standby);
    VALIDATE_STATE(Standby, Wait, Up);

    // switch mux to active state
    postMuxEvent(mux_state::MuxState::Standby);
    VALIDATE_STATE(Standby, Standby, Up);
}

TEST_F(LinkManagerStateMachineTest, MuxActiveSwitchOver)
{
    setMuxActive();

    // verify MUX enters wait state and that the diver is being probed
    EXPECT_EQ(mDbInterface.mProbeMuxStateInvokeCount, 0);
    EXPECT_EQ(mDbInterface.mGetMuxStateInvokeCount, 1);
    postLinkProberEvent(link_prober::LinkProberState::Standby);
    VALIDATE_STATE(Standby, Wait, Up);
    EXPECT_EQ(mDbInterface.mProbeMuxStateInvokeCount, 1);

    // fake mux statedb state to be active
    mDbInterface.setNextMuxState(mux_state::MuxState::Active);
    EXPECT_EQ(mDbInterface.mGetMuxStateInvokeCount, 1);
    // driver notification
    handleProbeMuxState("standby");
    VALIDATE_STATE(Standby, Standby, Up);
    EXPECT_EQ(mDbInterface.mGetMuxStateInvokeCount, 2);

    // get state db mux state
    EXPECT_EQ(mDbInterface.mSetMuxStateInvokeCount, 0);
    handleGetMuxState("active");
    VALIDATE_STATE(Standby, Wait, Up);
    EXPECT_EQ(mDbInterface.mSetMuxStateInvokeCount, 1);

    // swss notification
    handleMuxState("standby");
    VALIDATE_STATE(Standby, Standby, Up);
}

TEST_F(LinkManagerStateMachineTest, MuxStandbySwitchOver)
{
    setMuxStandby();

    // verify MUX enters wait state and that the diver is being probed
    EXPECT_EQ(mDbInterface.mProbeMuxStateInvokeCount, 0);
    EXPECT_EQ(mDbInterface.mGetMuxStateInvokeCount, 1);
    postLinkProberEvent(link_prober::LinkProberState::Active);
    VALIDATE_STATE(Active, Wait, Up);
    EXPECT_EQ(mDbInterface.mProbeMuxStateInvokeCount, 1);

    // fake mux statedb state to be standby
    mDbInterface.setNextMuxState(mux_state::MuxState::Standby);
    EXPECT_EQ(mDbInterface.mGetMuxStateInvokeCount, 1);
    // driver notification
    handleProbeMuxState("active");
    VALIDATE_STATE(Active, Active, Up);
    EXPECT_EQ(mDbInterface.mGetMuxStateInvokeCount, 2);

    // get state db mux state
    EXPECT_EQ(mDbInterface.mSetMuxStateInvokeCount, 0);
    handleGetMuxState("standby");
    VALIDATE_STATE(Active, Wait, Up);
    EXPECT_EQ(mDbInterface.mSetMuxStateInvokeCount, 1);

    // swss notification
    handleMuxState("active");
    VALIDATE_STATE(Active, Active, Up);
}

TEST_F(LinkManagerStateMachineTest, MuxActiveCliSwitchOver)
{
    setMuxActive();

    handleMuxConfig("active");
    VALIDATE_STATE(Active, Active, Up);
}

TEST_F(LinkManagerStateMachineTest, MuxStandbyCliSwitchOverMuxFirst)
{
    setMuxStandby();

    EXPECT_EQ(mDbInterface.mSetMuxStateInvokeCount, 0);
    handleMuxConfig("active", 2);

    VALIDATE_STATE(Wait, Wait, Up);
    EXPECT_EQ(mDbInterface.mSetMuxStateInvokeCount, 1);

    // swss notification
    handleMuxState("active", 3);
    VALIDATE_STATE(Wait, Active, Up);

    // swss notification
    handleProbeMuxState("active", 3);
    VALIDATE_STATE(Wait, Active, Up);

    // change state to active
    postLinkProberEvent(link_prober::LinkProberState::Active, 3);
    VALIDATE_STATE(Active, Active, Up);
}

TEST_F(LinkManagerStateMachineTest, MuxStandbyCliSwitchOverLinkProberFirst)
{
    setMuxStandby();

    EXPECT_EQ(mDbInterface.mSetMuxStateInvokeCount, 0);
    handleMuxConfig("active");

    VALIDATE_STATE(Wait, Wait, Up);
    EXPECT_EQ(mDbInterface.mSetMuxStateInvokeCount, 1);

    // change state to active
    postLinkProberEvent(link_prober::LinkProberState::Active);
    VALIDATE_STATE(Active, Wait, Up);

    // swss notification
    handleMuxState("active");
    VALIDATE_STATE(Active, Active, Up);
}

TEST_F(LinkManagerStateMachineTest, MuxActiveLinkDown)
{
    setMuxActive();

    EXPECT_EQ(mDbInterface.mSetMuxStateInvokeCount, 0);
    handleLinkState("down");

    VALIDATE_STATE(Active, Wait, Down);
    EXPECT_EQ(mDbInterface.mSetMuxStateInvokeCount, 1);

    // swss notification
    handleMuxState("standby");
    VALIDATE_STATE(Active, Standby, Down);

    handleLinkState("up");
    VALIDATE_STATE(Standby, Standby, Up);
}

TEST_F(LinkManagerStateMachineTest, MuxStandbyLinkDown)
{
    setMuxStandby();

    handleLinkState("down");
    VALIDATE_STATE(Standby, Standby, Down);

    handleLinkState("up");
    VALIDATE_STATE(Standby, Standby, Up);
}

} /* namespace test */
