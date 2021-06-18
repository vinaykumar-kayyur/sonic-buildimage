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
    mDbInterfacePtr(std::make_shared<FakeDbInterface> (&mIoService)),
    mFakeMuxPort(
        mDbInterfacePtr,
        mMuxConfig,
        mPortName,
        mServerId,
        mIoService
    )
{
    mMuxConfig.setTimeoutIpv4_msec(1);
    mMuxConfig.setPositiveStateChangeRetryCount(2);
//    mMuxConfig.setMuxStateChangeRetryCount(2);
    mMuxConfig.setLinkStateChangeRetryCount(2);
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
    switch (label) {
    case link_prober::LinkProberState::Active:
        for (uint8_t i = 0; i < mMuxConfig.getPositiveStateChangeRetryCount(); i++) {
            mFakeMuxPort.mFakeLinkProber->postLinkProberEvent<link_prober::IcmpSelfEvent&>(
                link_prober::LinkProberStateMachine::getIcmpSelfEvent()
            );
            runIoService(count);
        }
        break;
    case link_prober::LinkProberState::Standby:
        for (uint8_t i = 0; i < mMuxConfig.getPositiveStateChangeRetryCount(); i++) {
            mFakeMuxPort.mFakeLinkProber->postLinkProberEvent<link_prober::IcmpPeerEvent&>(
                link_prober::LinkProberStateMachine::getIcmpPeerEvent()
            );
            runIoService(count);
        }
        break;
    case link_prober::LinkProberState::Unknown:
        for (uint8_t i = 0; i < mMuxConfig.getNegativeStateChangeRetryCount(); i++) {
            mFakeMuxPort.mFakeLinkProber->postLinkProberEvent<link_prober::IcmpUnknownEvent&>(
                link_prober::LinkProberStateMachine::getIcmpUnknownEvent()
            );
            runIoService(count);
        }
        break;
    default:
        break;
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
        case mux_state::MuxState::Error:
            muxStateMachine.postMuxStateEvent(mux_state::MuxStateMachine::getErrorEvent());
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

void LinkManagerStateMachineTest::postSuspendTimerExpiredEvent(uint32_t count)
{
    mFakeMuxPort.mFakeLinkProber->postSuspendTimerExpiredEvent();
    runIoService(count);
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
    for (uint8_t i = 0; i < mMuxConfig.getLinkStateChangeRetryCount(); i++) {
        mFakeMuxPort.handleLinkState(linkState);
        runIoService();
    }
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
    VALIDATE_STATE(Unknown, Wait, Up);

    // change state to active
    postLinkProberEvent(link_prober::LinkProberState::Active);
    VALIDATE_STATE(Active, Wait, Up);

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
    VALIDATE_STATE(Unknown, Wait, Up);

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
    EXPECT_EQ(mDbInterfacePtr->mProbeMuxStateInvokeCount, 0);
    EXPECT_EQ(mDbInterfacePtr->mGetMuxStateInvokeCount, 1);
    postLinkProberEvent(link_prober::LinkProberState::Standby);
    VALIDATE_STATE(Standby, Wait, Up);
    EXPECT_EQ(mDbInterfacePtr->mProbeMuxStateInvokeCount, 1);

    // fake mux statedb state to be active
    mDbInterfacePtr->setNextMuxState(mux_state::MuxState::Active);
    EXPECT_EQ(mDbInterfacePtr->mGetMuxStateInvokeCount, 1);
    // driver notification
    handleProbeMuxState("standby");
    VALIDATE_STATE(Standby, Standby, Up);
    EXPECT_EQ(mDbInterfacePtr->mGetMuxStateInvokeCount, 2);

    // get state db mux state
    EXPECT_EQ(mDbInterfacePtr->mSetMuxStateInvokeCount, 0);
    handleGetMuxState("active");
    VALIDATE_STATE(Standby, Wait, Up);
    EXPECT_EQ(mDbInterfacePtr->mSetMuxStateInvokeCount, 1);

    // swss notification
    handleMuxState("standby");
    VALIDATE_STATE(Standby, Standby, Up);
}

TEST_F(LinkManagerStateMachineTest, MuxStandbySwitchOver)
{
    setMuxStandby();

    // Verify posting extra standby won't change link prober state
    postLinkProberEvent(link_prober::LinkProberState::Standby, 3);
    VALIDATE_STATE(Standby, Standby, Up);

    // verify MUX enters wait state and that the diver is being probed
    EXPECT_EQ(mDbInterfacePtr->mProbeMuxStateInvokeCount, 0);
    EXPECT_EQ(mDbInterfacePtr->mGetMuxStateInvokeCount, 1);
    postLinkProberEvent(link_prober::LinkProberState::Active);
    VALIDATE_STATE(Active, Wait, Up);
    EXPECT_EQ(mDbInterfacePtr->mProbeMuxStateInvokeCount, 1);

    // fake mux statedb state to be standby
    mDbInterfacePtr->setNextMuxState(mux_state::MuxState::Standby);
    EXPECT_EQ(mDbInterfacePtr->mGetMuxStateInvokeCount, 1);
    // driver notification
    handleProbeMuxState("active");
    VALIDATE_STATE(Active, Active, Up);
    EXPECT_EQ(mDbInterfacePtr->mGetMuxStateInvokeCount, 2);

    // get state db mux state
    EXPECT_EQ(mDbInterfacePtr->mSetMuxStateInvokeCount, 0);
    handleGetMuxState("standby");
    VALIDATE_STATE(Active, Wait, Up);
    EXPECT_EQ(mDbInterfacePtr->mSetMuxStateInvokeCount, 1);

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

TEST_F(LinkManagerStateMachineTest, MuxActiveCliAuto)
{
    setMuxActive();

    handleMuxConfig("auto");
    VALIDATE_STATE(Active, Active, Up);
}

TEST_F(LinkManagerStateMachineTest, MuxAStandbyCliAuto)
{
    setMuxStandby();

    handleMuxConfig("auto");
    VALIDATE_STATE(Standby, Standby, Up);
}

TEST_F(LinkManagerStateMachineTest, MuxActiveCliManual)
{
    setMuxActive();

    handleMuxConfig("manual");
    VALIDATE_STATE(Active, Active, Up);
}

TEST_F(LinkManagerStateMachineTest, MuxAStandbyCliManual)
{
    setMuxStandby();

    handleMuxConfig("manual");
    VALIDATE_STATE(Standby, Standby, Up);
}

TEST_F(LinkManagerStateMachineTest, MuxStandbyCliSwitchOverMuxFirst)
{
    setMuxStandby();

    EXPECT_EQ(mDbInterfacePtr->mSetMuxStateInvokeCount, 0);
    handleMuxConfig("active", 2);

    VALIDATE_STATE(Wait, Wait, Up);
    EXPECT_EQ(mDbInterfacePtr->mSetMuxStateInvokeCount, 1);

    // swss notification
    handleMuxState("active", 3);
    VALIDATE_STATE(Wait, Active, Up);

    // change state to active
    postLinkProberEvent(link_prober::LinkProberState::Active, 3);
    VALIDATE_STATE(Active, Wait, Up);

    // xcvrd notification
    handleProbeMuxState("active", 3);
    VALIDATE_STATE(Active, Active, Up);
}

TEST_F(LinkManagerStateMachineTest, MuxStandbyCliSwitchOverLinkProberFirst)
{
    setMuxStandby();

    EXPECT_EQ(mDbInterfacePtr->mSetMuxStateInvokeCount, 0);
    handleMuxConfig("active");

    VALIDATE_STATE(Wait, Wait, Up);
    EXPECT_EQ(mDbInterfacePtr->mSetMuxStateInvokeCount, 1);

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

    EXPECT_EQ(mDbInterfacePtr->mSetMuxStateInvokeCount, 0);
    handleLinkState("down");

    VALIDATE_STATE(Active, Wait, Down);
    EXPECT_EQ(mDbInterfacePtr->mSetMuxStateInvokeCount, 1);

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

TEST_F(LinkManagerStateMachineTest, MuxActiveLinkProberUnknownPeerOvertakeLink)
{
    setMuxActive();

    // verify MUX enters wait state and that the diver is being probed
    EXPECT_EQ(mDbInterfacePtr->mProbeMuxStateInvokeCount, 0);
    EXPECT_EQ(mDbInterfacePtr->mGetMuxStateInvokeCount, 1);
    postLinkProberEvent(link_prober::LinkProberState::Unknown);
    VALIDATE_STATE(Unknown, Active, Up);
    EXPECT_EQ(mFakeMuxPort.mFakeLinkProber->mSuspendTxProbeCallCount, 1);

    postSuspendTimerExpiredEvent();
    VALIDATE_STATE(Unknown, Wait, Up);
    EXPECT_EQ(mDbInterfacePtr->mProbeMuxStateInvokeCount, 1);

    // Verify posting extra unknown won't change link prober state
    postLinkProberEvent(link_prober::LinkProberState::Unknown, 3);
    VALIDATE_STATE(Unknown, Wait, Up);

    postLinkProberEvent(link_prober::LinkProberState::Standby);
    VALIDATE_STATE(Standby, Wait, Up);

    handleProbeMuxState("standby");
    VALIDATE_STATE(Standby, Standby, Up);
    EXPECT_EQ(mDbInterfacePtr->mGetMuxStateInvokeCount, 2);
}

TEST_F(LinkManagerStateMachineTest, MuxActiveLinkProberUnknownReturnActive)
{
    setMuxActive();

    // verify MUX enters wait state and that the diver is being probed
    EXPECT_EQ(mDbInterfacePtr->mProbeMuxStateInvokeCount, 0);
    EXPECT_EQ(mDbInterfacePtr->mGetMuxStateInvokeCount, 1);
    postLinkProberEvent(link_prober::LinkProberState::Unknown);
    VALIDATE_STATE(Unknown, Active, Up);
    EXPECT_EQ(mFakeMuxPort.mFakeLinkProber->mSuspendTxProbeCallCount, 1);

    postSuspendTimerExpiredEvent();
    VALIDATE_STATE(Unknown, Wait, Up);
    EXPECT_EQ(mDbInterfacePtr->mProbeMuxStateInvokeCount, 1);

    EXPECT_EQ(mDbInterfacePtr->mSetMuxStateInvokeCount, 0);
    handleProbeMuxState("standby");
    VALIDATE_STATE(Wait, Wait, Up);

    // ensure link prober stays in wait state if unknown event was posted
    postLinkProberEvent(link_prober::LinkProberState::Unknown);
    VALIDATE_STATE(Wait, Wait, Up);

    EXPECT_EQ(mDbInterfacePtr->mSetMuxStateInvokeCount, 1);
    // swss notification
    handleMuxState("active", 3);
    VALIDATE_STATE(Wait, Active, Up);

    // change state to active
    postLinkProberEvent(link_prober::LinkProberState::Active, 3);
    VALIDATE_STATE(Active, Wait, Up);

    // xcvrd notification
    handleProbeMuxState("active", 3);
    VALIDATE_STATE(Active, Active, Up);
}

TEST_F(LinkManagerStateMachineTest, MuxStandbyLinkProberUnknown)
{
    setMuxStandby();

    // verify MUX enters wait state and that the diver is being probed
    EXPECT_EQ(mDbInterfacePtr->mProbeMuxStateInvokeCount, 0);
    EXPECT_EQ(mDbInterfacePtr->mGetMuxStateInvokeCount, 1);
    EXPECT_EQ(mDbInterfacePtr->mSetMuxStateInvokeCount, 0);
    postLinkProberEvent(link_prober::LinkProberState::Unknown);
    VALIDATE_STATE(Wait, Wait, Up);
    EXPECT_EQ(mDbInterfacePtr->mSetMuxStateInvokeCount, 1);

    // swss notification
    handleMuxState("active", 3);
    VALIDATE_STATE(Wait, Active, Up);

    // change state to active
    postLinkProberEvent(link_prober::LinkProberState::Active, 3);
    VALIDATE_STATE(Active, Wait, Up);

    // xcvrd notification
    handleProbeMuxState("active", 3);
    VALIDATE_STATE(Active, Active, Up);
}

TEST_F(LinkManagerStateMachineTest, MuxStandbyLinkProberUnknownReturnStandby)
{
    setMuxStandby();

    // verify MUX enters wait state and that the diver is being probed
    EXPECT_EQ(mDbInterfacePtr->mProbeMuxStateInvokeCount, 0);
    EXPECT_EQ(mDbInterfacePtr->mGetMuxStateInvokeCount, 1);
    EXPECT_EQ(mDbInterfacePtr->mSetMuxStateInvokeCount, 0);
    postLinkProberEvent(link_prober::LinkProberState::Unknown);
    VALIDATE_STATE(Wait, Wait, Up);
    EXPECT_EQ(mDbInterfacePtr->mSetMuxStateInvokeCount, 1);

    // swss notification
    handleMuxState("standby", 3);
    VALIDATE_STATE(Wait, Standby, Up);

    // change state to standby
    postLinkProberEvent(link_prober::LinkProberState::Standby, 3);
    VALIDATE_STATE(Standby, Wait, Up);

    // xcvrd notification
    handleProbeMuxState("standby", 3);
    VALIDATE_STATE(Standby, Standby, Up);
}

TEST_F(LinkManagerStateMachineTest, MuxActiveAsymetricLinkDrop)
{
    setMuxActive();

    // verify MUX enters wait state and that the diver is being probed
    EXPECT_EQ(mDbInterfacePtr->mProbeMuxStateInvokeCount, 0);
    EXPECT_EQ(mDbInterfacePtr->mGetMuxStateInvokeCount, 1);
    postLinkProberEvent(link_prober::LinkProberState::Unknown);
    VALIDATE_STATE(Unknown, Active, Up);
    EXPECT_EQ(mFakeMuxPort.mFakeLinkProber->mSuspendTxProbeCallCount, 1);

    postSuspendTimerExpiredEvent();
    VALIDATE_STATE(Unknown, Wait, Up);
    EXPECT_EQ(mDbInterfacePtr->mProbeMuxStateInvokeCount, 1);

    // Peer took over the link
    handleProbeMuxState("standby", 3);
    VALIDATE_STATE(Wait, Wait, Up);
    EXPECT_EQ(mDbInterfacePtr->mGetMuxStateInvokeCount, 1);

    EXPECT_EQ(mDbInterfacePtr->mSetMuxStateInvokeCount, 1);
    // swss notification
    handleMuxState("active", 3);
    VALIDATE_STATE(Wait, Active, Up);
    EXPECT_EQ(mDbInterfacePtr->mGetMuxStateInvokeCount, 2);

    runIoService();
    VALIDATE_STATE(Wait, Wait, Up);

    handleProbeMuxState("active", 3);
    VALIDATE_STATE(Wait, Active, Up);
    EXPECT_EQ(mDbInterfacePtr->mGetMuxStateInvokeCount, 3);
    EXPECT_EQ(mFakeMuxPort.mFakeLinkProber->mSuspendTxProbeCallCount, 2);

    runIoService();
    VALIDATE_STATE(Wait, Wait, Up);

    handleProbeMuxState("standby", 3);
    VALIDATE_STATE(Wait, Standby, Up);
    EXPECT_EQ(mDbInterfacePtr->mGetMuxStateInvokeCount, 4);
    EXPECT_EQ(mFakeMuxPort.mFakeLinkProber->mSuspendTxProbeCallCount, 2);
}

TEST_F(LinkManagerStateMachineTest, MuxStandbyAsymetricLinkDrop)
{
    setMuxStandby();

    // verify MUX enters wait state and that the diver is being probed
    EXPECT_EQ(mDbInterfacePtr->mProbeMuxStateInvokeCount, 0);
    EXPECT_EQ(mDbInterfacePtr->mGetMuxStateInvokeCount, 1);
    postLinkProberEvent(link_prober::LinkProberState::Unknown);
    VALIDATE_STATE(Wait, Wait, Up);

    EXPECT_EQ(mDbInterfacePtr->mSetMuxStateInvokeCount, 1);
    // swss notification
    handleMuxState("active", 3);
    VALIDATE_STATE(Wait, Active, Up);
    EXPECT_EQ(mDbInterfacePtr->mGetMuxStateInvokeCount, 2);

    runIoService();
    VALIDATE_STATE(Wait, Wait, Up);

    handleProbeMuxState("active", 3);
    VALIDATE_STATE(Wait, Active, Up);
    EXPECT_EQ(mDbInterfacePtr->mGetMuxStateInvokeCount, 3);
    EXPECT_EQ(mFakeMuxPort.mFakeLinkProber->mSuspendTxProbeCallCount, 1);

    runIoService();
    VALIDATE_STATE(Wait, Wait, Up);

    handleProbeMuxState("standby", 3);
    VALIDATE_STATE(Wait, Standby, Up);
    EXPECT_EQ(mDbInterfacePtr->mGetMuxStateInvokeCount, 4);
    EXPECT_EQ(mFakeMuxPort.mFakeLinkProber->mSuspendTxProbeCallCount, 1);
}

TEST_F(LinkManagerStateMachineTest, ActiveStateToProberUnknownMuxUnknownLinkUp)
{
    setMuxActive();

    postMuxEvent(mux_state::MuxState::Unknown);
    VALIDATE_STATE(Active, Wait, Up);

    // xcvrd notification
    handleProbeMuxState("unknown", 3);
    VALIDATE_STATE(Active, Wait, Up);

    postLinkProberEvent(link_prober::LinkProberState::Unknown);
    handleProbeMuxState("unknown", 3);
    VALIDATE_STATE(Unknown, Unknown, Up);

    runIoService();
    VALIDATE_STATE(Unknown, Wait, Up);

    // xcvrd notification
    handleProbeMuxState("unknown", 3);
    VALIDATE_STATE(Unknown, Unknown, Up);

    runIoService();
    VALIDATE_STATE(Unknown, Wait, Up);

    handleProbeMuxState("active", 3);
    VALIDATE_STATE(Unknown, Active, Up);
    EXPECT_EQ(mDbInterfacePtr->mGetMuxStateInvokeCount, 4);
    EXPECT_EQ(mFakeMuxPort.mFakeLinkProber->mSuspendTxProbeCallCount, 1);

    postLinkProberEvent(link_prober::LinkProberState::Active);
    VALIDATE_STATE(Active, Active, Up);
}

TEST_F(LinkManagerStateMachineTest, StandbyStateToProberUnknownMuxUnknownLinkUp)
{
    setMuxStandby();

    postMuxEvent(mux_state::MuxState::Unknown);
    VALIDATE_STATE(Standby, Wait, Up);

    // xcvrd notification
    handleProbeMuxState("unknown", 3);
    VALIDATE_STATE(Standby, Wait, Up);

    postLinkProberEvent(link_prober::LinkProberState::Unknown);
    handleProbeMuxState("unknown", 3);
    VALIDATE_STATE(Unknown, Unknown, Up);

    runIoService();
    VALIDATE_STATE(Unknown, Wait, Up);

    // xcvrd notification
    handleProbeMuxState("unknown", 3);
    VALIDATE_STATE(Unknown, Unknown, Up);

    runIoService();
    VALIDATE_STATE(Unknown, Wait, Up);

    EXPECT_EQ(mDbInterfacePtr->mSetMuxStateInvokeCount, 0);
    handleProbeMuxState("standby", 3);
    VALIDATE_STATE(Wait, Wait, Up);
    EXPECT_EQ(mDbInterfacePtr->mSetMuxStateInvokeCount, 1);

    // swss notification
    handleMuxState("unknown");
    VALIDATE_STATE(Wait, Wait, Up);

    postLinkProberEvent(link_prober::LinkProberState::Active);
    VALIDATE_STATE(Active, Wait, Up);

    // xcvrd notification
    handleProbeMuxState("active");
    VALIDATE_STATE(Active, Active, Up);
}

TEST_F(LinkManagerStateMachineTest, ProberUnknownMuxUnknownLinkDown)
{
    setMuxActive();

    EXPECT_EQ(mDbInterfacePtr->mSetMuxStateInvokeCount, 0);
    handleLinkState("down");

    VALIDATE_STATE(Active, Wait, Down);
    EXPECT_EQ(mDbInterfacePtr->mSetMuxStateInvokeCount, 1);

    // swss notification
    handleMuxState("unknown");
    VALIDATE_STATE(Active, Unknown, Down);

    postLinkProberEvent(link_prober::LinkProberState::Unknown);
    VALIDATE_STATE(Unknown, Wait, Down);

    handleProbeMuxState("unknown");
    VALIDATE_STATE(Unknown, Wait, Down);
}

TEST_F(LinkManagerStateMachineTest, ProberWaitMuxUnknownLinkDown)
{
    setMuxStandby();

    postMuxEvent(mux_state::MuxState::Unknown);
    VALIDATE_STATE(Standby, Wait, Up);

    // xcvrd notification
    handleProbeMuxState("unknown", 3);
    VALIDATE_STATE(Standby, Wait, Up);

    postLinkProberEvent(link_prober::LinkProberState::Unknown);
    handleProbeMuxState("unknown", 3);
    VALIDATE_STATE(Unknown, Unknown, Up);

    runIoService();
    VALIDATE_STATE(Unknown, Wait, Up);

    // xcvrd notification
    handleProbeMuxState("unknown", 3);
    VALIDATE_STATE(Unknown, Unknown, Up);

    runIoService();
    VALIDATE_STATE(Unknown, Wait, Up);

    EXPECT_EQ(mDbInterfacePtr->mSetMuxStateInvokeCount, 0);
    handleProbeMuxState("standby", 3);
    VALIDATE_STATE(Wait, Wait, Up);
    EXPECT_EQ(mDbInterfacePtr->mSetMuxStateInvokeCount, 1);

    // swss notification
    handleMuxState("unknown");
    VALIDATE_STATE(Wait, Wait, Up);

    handleLinkState("down");
    VALIDATE_STATE(Wait, Wait, Down);

    // xcvrd notification
    handleProbeMuxState("unknown", 3);
    VALIDATE_STATE(Wait, Unknown, Down);

    runIoService();
    VALIDATE_STATE(Wait, Wait, Down);

}

} /* namespace test */
