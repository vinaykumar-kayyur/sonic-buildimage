/*
 * LinkManagerStateMachine.cpp
 *
 *  Created on: Oct 18, 2020
 *      Author: tamer
 */

#include <boost/bind/bind.hpp>

#include "link_manager/LinkManagerStateMachine.h"
#include "common/MuxLogger.h"
#include "MuxPort.h"

#define LOG_MUX_STATE_TRANSITION(portName, currentState, nextState) \
    do { \
            MUXLOGINFO(boost::format("%s: (P: %s, M: %s, L: %s) -> (P: %s, M: %s, L: %s)") % \
            portName % \
            mLinkProberStateName[ps(currentState)] % \
            mMuxStateName[ms(currentState)] % \
            mLinkStateName[ls(currentState)] % \
            mLinkProberStateName[ps(nextState)] % \
            mMuxStateName[ms(nextState)] % \
            mLinkStateName[ls(nextState)] \
        ); \
    } while (0)

namespace link_manager
{

LinkManagerStateMachine::TransitionFunction
    LinkManagerStateMachine::mStateTransitionHandler[link_prober::LinkProberState::Label::Count]
                                                    [mux_state::MuxState::Label::Count]
                                                    [link_state::LinkState::Label::Count];

LinkProberEvent LinkManagerStateMachine::mLinkProberEvent;
MuxStateEvent LinkManagerStateMachine::mMuxStateEvent;
LinkStateEvent LinkManagerStateMachine::mLinkStateEvent;

std::vector<std::string> LinkManagerStateMachine::mLinkProberStateName = {"Active", "Standby", "Unknown", "Wait"};
std::vector<std::string> LinkManagerStateMachine::mMuxStateName = {"Active", "Standby", "Unknown", "Wait"};
std::vector<std::string> LinkManagerStateMachine::mLinkStateName = {"Up", "Down"};

//
// ---> LinkManagerStateMachine(
//          mux::MuxPort *muxPortPtr,
//          boost::asio::io_service::strand &strand,
//          common::MuxPortConfig &muxPortConfig
//      );
//
// class constructor
//
LinkManagerStateMachine::LinkManagerStateMachine(
    mux::MuxPort *muxPortPtr,
    boost::asio::io_service::strand &strand,
    common::MuxPortConfig &muxPortConfig
) :
    StateMachine(strand, muxPortConfig),
    mMuxPortPtr(muxPortPtr),
    mLinkProberStateMachine(*this, strand, muxPortConfig, ps(mCompositeState)),
    mMuxStateMachine(*this, strand, muxPortConfig, ms(mCompositeState)),
    mLinkStateMachine(*this, strand, muxPortConfig, ls(mCompositeState))
{
    assert(muxPortPtr != nullptr);
    mMuxStateMachine.setWaitStateCause(mux_state::WaitState::WaitStateCause::SwssUpdate);
}

//
// ---> initializeTransitionFunctionTable()
//
// initialize static transition function table
//
void LinkManagerStateMachine::initializeTransitionFunctionTable()
{
    MUXLOGINFO("Initializing State Transition Table...");
    for (uint8_t linkProberState = link_prober::LinkProberState::Label::Active;
            linkProberState < link_prober::LinkProberState::Label::Count; linkProberState++) {
        for (uint8_t muxState = mux_state::MuxState::Label::Active;
                muxState < mux_state::MuxState::Label::Count; muxState++) {
            for (uint8_t linkState = link_state::LinkState::Label::Up;
                    linkState < link_state::LinkState::Label::Count; linkState++) {
                mStateTransitionHandler[linkProberState][muxState][linkState] =
                    boost::bind(
                        &LinkManagerStateMachine::noopTransitionFunction,
                        boost::placeholders::_1,
                        boost::placeholders::_2
                    );
            }
        }
    }

    mStateTransitionHandler[link_prober::LinkProberState::Label::Standby]
                           [mux_state::MuxState::Label::Active]
                           [link_state::LinkState::Label::Up] =
        boost::bind(
            &LinkManagerStateMachine::LinkProberStandbyMuxActiveLinkUpTransitionFunction,
            boost::placeholders::_1,
            boost::placeholders::_2
        );
    mStateTransitionHandler[link_prober::LinkProberState::Label::Unknown]
                           [mux_state::MuxState::Label::Active]
                           [link_state::LinkState::Label::Up] =
        boost::bind(
            &LinkManagerStateMachine::LinkProberUnknownMuxActiveLinkUpTransitionFunction,
            boost::placeholders::_1,
            boost::placeholders::_2
        );
    mStateTransitionHandler[link_prober::LinkProberState::Label::Active]
                           [mux_state::MuxState::Label::Standby]
                           [link_state::LinkState::Label::Up] =
        boost::bind(
            &LinkManagerStateMachine::LinkProberActiveMuxStandbyLinkUpTransitionFunction,
            boost::placeholders::_1,
            boost::placeholders::_2
        );
    mStateTransitionHandler[link_prober::LinkProberState::Label::Unknown]
                           [mux_state::MuxState::Label::Standby]
                           [link_state::LinkState::Label::Up] =
        boost::bind(
            &LinkManagerStateMachine::LinkProberUnknownMuxStandbyLinkUpTransitionFunction,
            boost::placeholders::_1,
            boost::placeholders::_2
        );
    mStateTransitionHandler[link_prober::LinkProberState::Label::Active]
                           [mux_state::MuxState::Label::Unknown]
                           [link_state::LinkState::Label::Up] =
        boost::bind(
            &LinkManagerStateMachine::LinkProberActiveMuxUnknownLinkUpTransitionFunction,
            boost::placeholders::_1,
            boost::placeholders::_2
        );
    mStateTransitionHandler[link_prober::LinkProberState::Label::Standby]
                           [mux_state::MuxState::Label::Unknown]
                           [link_state::LinkState::Label::Up] =
        boost::bind(
            &LinkManagerStateMachine::LinkProberStandbyMuxUnknownLinkUpTransitionFunction,
            boost::placeholders::_1,
            boost::placeholders::_2
        );
//    mStateTransitionHandler[link_prober::LinkProberState::Label::Active]
//                           [mux_state::MuxState::Label::Active]
//                           [link_state::LinkState::Label::Down] =
//        boost::bind(
//            &LinkManagerStateMachine::LinkProberActiveMuxActiveLinkDownTransitionFunction,
//            boost::placeholders::_1,
//            boost::placeholders::_2
//        );
}

//
// ---> enterLinkProberState(CompositeState &nextState, link_prober::LinkProberState::Label label);
//
// force LinkProberState to switch state
//
void LinkManagerStateMachine::enterLinkProberState(CompositeState &nextState, link_prober::LinkProberState::Label label)
{
    mLinkProberStateMachine.enterState(label);
    ps(nextState) = label;
}

//
// ---> enterMuxState(CompositeState &nextState, mux_state::MuxState::Label label);
//
// force MuxState to switch state
//
void LinkManagerStateMachine::enterMuxState(CompositeState &nextState, mux_state::MuxState::Label label)
{
    mMuxStateMachine.enterState(label);
    ms(nextState) = label;
}

//
// ---> enterLinkState(CompositeState &nextState, link_state::LinkState::Label label);
//
// force LinkState to switch state
//
void LinkManagerStateMachine::enterLinkState(CompositeState &nextState, link_state::LinkState::Label label)
{
    mLinkStateMachine.enterState(label);
    ls(nextState) = label;
}

//
// ---> enterMuxWaitState(CompositeState &nextState);
//
// force MuxState to switch to WaitState
//
void LinkManagerStateMachine::enterMuxWaitState(CompositeState &nextState)
{
    enterMuxState(nextState, mux_state::MuxState::Label::Wait);
    mMuxStateMachine.setWaitStateCause(mux_state::WaitState::WaitStateCause::DriverUpdate);
    mMuxPortPtr->probeMuxState();
}

//
// ---> switchMuxState(CompositeState &nextState, mux_state::MuxState::Label label);
//
// switch Mux to switch via xcvrd to state label provider
//
void LinkManagerStateMachine::switchMuxState(CompositeState &nextState, mux_state::MuxState::Label label)
{
    enterMuxState(nextState, mux_state::MuxState::Label::Wait);
    mMuxStateMachine.setWaitStateCause(mux_state::WaitState::WaitStateCause::SwssUpdate);
    mMuxPortPtr->setMuxState(label);
}

//
// ---> initializeLinkProber();
//
// initialize LinkProber component. Note if this is the last component to be initialized,
//  state machine will be activated
//
void LinkManagerStateMachine::initializeLinkProber()
{
    if (!mComponentInitState.test(LinkProberComponent)) {
        mLinkProberPtr = std::make_shared<link_prober::LinkProber> (
            mMuxPortConfig,
            getStrand().context(),
            mLinkProberStateMachine
        );
        mComponentInitState.set(LinkProberComponent);

        activateStateMachine();
    }
}

//
// ---> activateStateMachine();
//
// activate the state machine by starting the LinkProber. This should be done after all
// components have been initialized.
//
void LinkManagerStateMachine::activateStateMachine()
{
    if (mComponentInitState.all()) {
        std::array<uint8_t, ETHER_ADDR_LEN> macAddress = mMuxPortConfig.getBladeMacAddress();
        std::array<char, 3 * ETHER_ADDR_LEN> macAddressStr = {0};

        snprintf(
            macAddressStr.data(), macAddressStr.size(), "%02x:%02x:%02x:%02x:%02x:%02x",
            macAddress[0], macAddress[1], macAddress[2], macAddress[3], macAddress[4], macAddress[5]
        );

        MUXLOGWARNING(boost::format("%s: MUX port link prober initialized with server IP: %s, server MAC: %s") %
            mMuxPortConfig.getPortName() %
            mMuxPortConfig.getBladeIpv4Address().to_string() %
            macAddressStr.data()
        );
        // make link prober state match the MUX state since the state machine is activated for the first time
        CompositeState nextState = mCompositeState;
        initLinkProberState(nextState);
        LOG_MUX_STATE_TRANSITION(mMuxPortConfig.getPortName(), mCompositeState, nextState);
        mCompositeState = nextState;

        mLinkProberPtr->initialize();
        mLinkProberPtr->startProbing();
    }
}

//
// ---> handleStateChange(LinkProberEvent &event, link_prober::LinkProberState::Label state);
//
// handles LinkProverEvent
//
void LinkManagerStateMachine::handleStateChange(LinkProberEvent &event, link_prober::LinkProberState::Label state)
{
    if ((dynamic_cast<link_prober::LinkProberState *> (mLinkProberStateMachine.getCurrentState()))->getStateLabel() == state) {
        MUXLOGINFO(boost::format("%s: Received link prober event, new state: %s") %
            mMuxPortConfig.getPortName() %
            mLinkProberStateName[state]
        );

        CompositeState nextState = mCompositeState;
        ps(nextState) = state;
        mStateTransitionHandler[ps(nextState)][ms(nextState)][ls(nextState)](this, nextState);
        LOG_MUX_STATE_TRANSITION(mMuxPortConfig.getPortName(), mCompositeState, nextState);
        mCompositeState = nextState;
    }
}

//
// ---> handleStateChange(MuxStateEvent &event, mux_state::MuxState::Label state);
//
// handles MuxStateEvent
//
void LinkManagerStateMachine::handleStateChange(MuxStateEvent &event, mux_state::MuxState::Label state)
{
    if ((dynamic_cast<mux_state::MuxState *> (mMuxStateMachine.getCurrentState()))->getStateLabel() == state) {
        MUXLOGINFO(boost::format("%s: Received mux state event, new state: %s") %
            mMuxPortConfig.getPortName() %
            mMuxStateName[state]
        );

        CompositeState nextState = mCompositeState;
        ms(nextState) = state;
        mStateTransitionHandler[ps(nextState)][ms(nextState)][ls(nextState)](this, nextState);
        LOG_MUX_STATE_TRANSITION(mMuxPortConfig.getPortName(), mCompositeState, nextState);
        mCompositeState = nextState;
    }

    if (ms(mCompositeState) != mux_state::MuxState::Wait) {
        // Verify if state db MUX state matches the driver/current MUX state
        mMuxPortPtr->getMuxState();
    }
}

//
// ---> handleStateChange(LinkStateEvent &event, link_state::LinkState::Label state);
//
// handles LinkStateEvent
//
void LinkManagerStateMachine::handleStateChange(LinkStateEvent &event, link_state::LinkState::Label state)
{
    if ((dynamic_cast<link_state::LinkState *> (mLinkStateMachine.getCurrentState()))->getStateLabel() == state) {
        MUXLOGINFO(boost::format("%s: Received link state event, new state: %s") %
            mMuxPortConfig.getPortName() %
            mLinkStateName[state]
        );

        CompositeState nextState = mCompositeState;
        ls(nextState) = state;
        if (ls(mCompositeState) == link_state::LinkState::Down &&
            ls(nextState) == link_state::LinkState::Up) {
            // start fresh when the link transition from Down to UP state
            // and so the link prober will initially match the MUX state
            // There is a problem with this approach as it will hide link flaps that result in lost heart-beats.
            initLinkProberState(nextState);
//            enterMuxWaitState(nextState);
        }
        else if (ls(mCompositeState) == link_state::LinkState::Up &&
                 ls(nextState) == link_state::LinkState::Down &&
                 ms(mCompositeState) == mux_state::MuxState::Label::Active &&
                 mMuxPortConfig.getMode() == common::MuxPortConfig::Mode::Auto) {
            // switch MUX to standby since we are entering LinkDown state
            switchMuxState(nextState, mux_state::MuxState::Label::Standby);
        }
        else {
            mStateTransitionHandler[ps(nextState)][ms(nextState)][ls(nextState)](this, nextState);
        }
        LOG_MUX_STATE_TRANSITION(mMuxPortConfig.getPortName(), mCompositeState, nextState);
        mCompositeState = nextState;
    }
}

//
// ---> handleGetServerMacAddressNotification(std::array<uint8_t, ETHER_ADDR_LEN> address);
//
// handle get Server MAC address
//
void LinkManagerStateMachine::handleGetServerMacAddressNotification(std::array<uint8_t, ETHER_ADDR_LEN> address)
{
    MUXLOGDEBUG(mMuxPortConfig.getPortName());
    if (!mComponentInitState.test(ServerMacComponent)) {
        mMuxPortConfig.setBladeMacAddress(address);

        mComponentInitState.set(ServerMacComponent);
        activateStateMachine();
    }
}

//
// ---> handleGetMuxStateNotification(mux_state::MuxState::Label label);
//
// handle get MUX state notification
//
void LinkManagerStateMachine::handleGetMuxStateNotification(mux_state::MuxState::Label label)
{
    MUXLOGDEBUG(boost::format("%s: state db mux state: %d") % mMuxPortConfig.getPortName() % label);

    if (mComponentInitState.all() && ms(mCompositeState) != label &&
        ms(mCompositeState) != mux_state::MuxState::Wait) {
        // notify swss of mux state change
        MUXLOGWARNING(boost::format("%s: Switching MUX state from '%s' to '%s' to match linkmgrd/driver state") %
                mMuxPortConfig.getPortName() %
                mMuxStateName[label] %
                mMuxStateName[ms(mCompositeState)]
        );
        switchMuxState(mCompositeState, ms(mCompositeState));
    }
}

//
// ---> handleProbeMuxStateNotification(mux_state::MuxState::Label label);
//
// handle MUX state notification. Source of notification could be state_db via
// orchagent or app_db via xcvrd
//
void LinkManagerStateMachine::handleProbeMuxStateNotification(mux_state::MuxState::Label label)
{
    MUXLOGDEBUG(boost::format("%s: state db mux state: %d") % mMuxPortConfig.getPortName() % label);

    if (mComponentInitState.all()) {
        if (mMuxStateMachine.getWaitStateCause() != mux_state::WaitState::WaitStateCause::DriverUpdate ||
            ms(mCompositeState) != mux_state::MuxState::Wait) {
            MUXLOGERROR(boost::format("%s: Received unsolicited MUX state probe notification!") %
                mMuxPortConfig.getPortName()
            );
        }

        postMuxStateEvent(label);
    } else {
        enterMuxState(mCompositeState, label);

        mComponentInitState.set(MuxStateComponent);
        activateStateMachine();
    }
}

//
// ---> handleMuxStateNotification(mux_state::MuxState::Label label);
//
// handle MUX state notification. Source of notification could be state_db via
// orchagent or app_db via xcvrd
//
void LinkManagerStateMachine::handleMuxStateNotification(mux_state::MuxState::Label label)
{
    MUXLOGDEBUG(boost::format("%s: state db mux state: %d") % mMuxPortConfig.getPortName() % label);

    if (mComponentInitState.all()) {
        if (mMuxStateMachine.getWaitStateCause() != mux_state::WaitState::WaitStateCause::SwssUpdate ||
            ms(mCompositeState) != mux_state::MuxState::Wait) {
            MUXLOGERROR(boost::format("%s: Received unsolicited MUX state change notification!") %
                mMuxPortConfig.getPortName()
            );
        }

        postMuxStateEvent(label);
    } else {
        enterMuxState(mCompositeState, label);

        mComponentInitState.set(MuxStateComponent);
        activateStateMachine();
    }
}

//
// ---> handleSwssLinkStateNotification(const link_state::LinkState::Label label);
//
// handle link state change notification
//
void LinkManagerStateMachine::handleSwssLinkStateNotification(const link_state::LinkState::Label label)
{
    MUXLOGDEBUG(boost::format("%s: state db link state: %d") % mMuxPortConfig.getPortName() % label);

    if (mComponentInitState.all()) {
        if (label == link_state::LinkState::Label::Up) {
            mLinkStateMachine.postLinkStateEvent(link_state::LinkStateMachine::getUpEvent());
        }
        else if (label == link_state::LinkState::Label::Down) {
            mLinkStateMachine.postLinkStateEvent(link_state::LinkStateMachine::getDownEvent());
        }
    } else {
        enterLinkState(mCompositeState, label);

        mComponentInitState.set(LinkStateComponent);
        activateStateMachine();
    }
}

//
// ---> handleMuxConfigNotification(const common::MuxPortConfig::Mode mode);
//
// handle MUX configuration change notification
//
void LinkManagerStateMachine::handleMuxConfigNotification(const common::MuxPortConfig::Mode mode)
{
    if (mComponentInitState.all() &&
        mode == common::MuxPortConfig::Mode::Active &&
        ps(mCompositeState) == link_prober::LinkProberState::Label::Standby &&
        ms(mCompositeState) == mux_state::MuxState::Label::Standby) {
        CompositeState nextState = mCompositeState;
        enterLinkProberState(nextState, link_prober::LinkProberState::Wait);
        switchMuxState(nextState, mux_state::MuxState::Label::Active);
        LOG_MUX_STATE_TRANSITION(mMuxPortConfig.getPortName(), mCompositeState, nextState);
        mCompositeState = nextState;
    }
}

//
// ---> handleSuspendTimerExpiry();
//
// handle suspend timer expiry notification from LinkProber
//
void LinkManagerStateMachine::handleSuspendTimerExpiry()
{
    // Note: suspend timer is started when Mux state is active and link is in unknown state.
    //       If standby (peer) ToR fails to pull the link, this ToR will loop between those states
    //       Prober: Unknown, Mux: Active, Link: Up -> Wait, Active, UP --Timer Expires--> Unknown, Wait, UP ->
    //               Unknown, Active, Up
    if (ps(mCompositeState) == link_prober::LinkProberState::Label::Wait) {
        CompositeState nextState = mCompositeState;
        // if we are still in wait state, enter an actionable state. This is required to handle
        // a corner case where peer ToR switches MUX, however peer ToR is not sending probes
//        enterLinkProberState(mCompositeState, link_prober::LinkProberState::Label::Unknown);
        initLinkProberState(mCompositeState);

        enterMuxWaitState(nextState);
        LOG_MUX_STATE_TRANSITION(mMuxPortConfig.getPortName(), mCompositeState, nextState);
        mCompositeState = nextState;
    }
}

//
// ---> initLinkProberState(CompositeState &compositeState);
//
// initialize LinkProberState when configuring the composite state machine
//
void LinkManagerStateMachine::initLinkProberState(CompositeState &compositeState)
{
    switch (ms(compositeState)) {
    case mux_state::MuxState::Label::Active:
        enterLinkProberState(compositeState, link_prober::LinkProberState::Label::Active);
        break;
    case mux_state::MuxState::Label::Standby:
        enterLinkProberState(compositeState, link_prober::LinkProberState::Label::Standby);
        break;
    case mux_state::MuxState::Label::Unknown:
        enterLinkProberState(compositeState, link_prober::LinkProberState::Label::Unknown);
        break;
    default:
        break;
    }
}

//
// ---> postMuxStateEvent(mux_state::MuxState::Label label)
//
// post event to MUX state machine to change state
//
void LinkManagerStateMachine::postMuxStateEvent(mux_state::MuxState::Label label)
{
    switch (label) {
    case mux_state::MuxState::Label::Active:
        mMuxStateMachine.postMuxStateEvent(mux_state::MuxStateMachine::getActiveEvent());
        break;
    case mux_state::MuxState::Label::Standby:
        mMuxStateMachine.postMuxStateEvent(mux_state::MuxStateMachine::getStandbyEvent());
        break;
    case mux_state::MuxState::Label::Unknown:
        mMuxStateMachine.postMuxStateEvent(mux_state::MuxStateMachine::getUnknownEvent());
        break;
    default:
        break;
    }
}

//
// ---> noopTransitionFunction(CompositeState &nextState);
//
// No-op transition function
//
void LinkManagerStateMachine::noopTransitionFunction(CompositeState &nextState)
{
    MUXLOGDEBUG(mMuxPortConfig.getPortName());
}

//
// ---> LinkProberStandbyMuxActiveLinkUpTransitionFunction(CompositeState &nextState);
//
// transition function when entering {LinkProberUnknown, MuxActive, LinkUp} state
//
void LinkManagerStateMachine::LinkProberStandbyMuxActiveLinkUpTransitionFunction(
    CompositeState &nextState
)
{
    MUXLOGINFO(mMuxPortConfig.getPortName());
    // Probe the MUX state as internal MUX state is active while LP reports standby link
    enterMuxWaitState(nextState);
}

//
// ---> LinkProberUnknownMuxActiveLinkUpTransitionFunction(CompositeState &nextState);
//
// transition function when entering {LinkProberUnknown, MuxActive, LinkUp} state
//
void LinkManagerStateMachine::LinkProberUnknownMuxActiveLinkUpTransitionFunction(
    CompositeState &nextState
)
{
    MUXLOGINFO(mMuxPortConfig.getPortName());
    // trigger LINKMANAGER_CHECK and transition to LinkWait state, suspend prober
    mLinkProberPtr->suspendTxProbes(mMuxPortConfig.getLinkWaitTimeout_msec());
    enterLinkProberState(nextState, link_prober::LinkProberState::Wait);

    enterMuxWaitState(nextState);
}

//
// ---> LinkProberActiveMuxStandbyLinkUpTransitionFunction(CompositeState &nextState);
//
// transition function when entering {LinkProberActive, MuxStandby, LinkUp} state
//
void LinkManagerStateMachine::LinkProberActiveMuxStandbyLinkUpTransitionFunction(
    CompositeState &nextState
)
{
    MUXLOGINFO(mMuxPortConfig.getPortName());
    enterMuxWaitState(nextState);
}

//
// ---> LinkProberUnknownMuxStandbyLinkUpTransitionFunction(CompositeState &nextState);
//
// transition function when entering {LinkProberUnknown, MuxStandby, LinkUp} state
//
void LinkManagerStateMachine::LinkProberUnknownMuxStandbyLinkUpTransitionFunction(
    CompositeState &nextState
)
{
    MUXLOGINFO(mMuxPortConfig.getPortName());
    enterLinkProberState(nextState, link_prober::LinkProberState::Wait);

    // Start switching MUX to active state as we lost HB from active ToR
    switchMuxState(nextState, mux_state::MuxState::Label::Active);
}

//
// ---> LinkProberActiveMuxUnknownLinkUpTransitionFunction(CompositeState &nextState);
//
// transition function when entering {LinkProberActive, MuxUnknown, LinkUp} state
//
void LinkManagerStateMachine::LinkProberActiveMuxUnknownLinkUpTransitionFunction(
    CompositeState &nextState
)
{
    MUXLOGINFO(mMuxPortConfig.getPortName());
    enterMuxWaitState(nextState);
}

//
// ---> LinkProberStandbyMuxUnknownLinkUpTransitionFunction(CompositeState &nextState);
//
// transition function when entering {LinkProberStandby, MuxUnknown, LinkUp} state
//
void LinkManagerStateMachine::LinkProberStandbyMuxUnknownLinkUpTransitionFunction(
    CompositeState &nextState
)
{
    MUXLOGINFO(mMuxPortConfig.getPortName());
    enterMuxWaitState(nextState);
}

//
// ---> LinkProberActiveMuxActiveLinkDownTransitionFunction(CompositeState &nextState);
//
// transition function when entering {LinkProberActive, MuxActive, LinkDown} state
//
void LinkManagerStateMachine::LinkProberActiveMuxActiveLinkDownTransitionFunction(CompositeState &nextState)
{
    MUXLOGINFO(mMuxPortConfig.getPortName());

    // Start switching MUX to standby as we lost the link
    switchMuxState(nextState, mux_state::MuxState::Label::Standby);
}

} /* namespace link_manager */
