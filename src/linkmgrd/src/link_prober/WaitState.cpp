/*
 * WaitState.cpp
 *
 *  Created on: Oct 18, 2020
 *      Author: tamer
 */

#include "link_prober/ActiveState.h"
#include "link_prober/StandbyState.h"
#include "link_prober/WaitState.h"
#include "link_prober/LinkProberStateMachine.h"

#include "common/MuxLogger.h"

namespace link_prober
{

//
// ---> WaitState(LinkProberStateMachine &stateMachine, common::MuxPortConfig &muxPortConfig);
//
// class constructor
//
WaitState::WaitState(
    LinkProberStateMachine &stateMachine,
    common::MuxPortConfig &muxPortConfig
) :
    LinkProberState(stateMachine, muxPortConfig)
{
}

//
// ---> handleEvent(IcmpPeerEvent &event);
//
// handle IcmpPeerEvent from LinkProber
//
LinkProberState* WaitState::handleEvent(IcmpPeerEvent &event)
{
    MUXLOGDEBUG(getMuxPortConfig().getPortName());

    LinkProberStateMachine *stateMachine = dynamic_cast<LinkProberStateMachine *> (getStateMachine());
    LinkProberState *nextState;

    mSelfEventCount = 0;
    if (++mPeerEventCount >= getMuxPortConfig().getPositiveStateChangeRetryCount()) {
        nextState = dynamic_cast<LinkProberState *> (stateMachine->getStandbyState());
    }
    else {
        nextState = dynamic_cast<LinkProberState *> (stateMachine->getWaitState());
    }

    return nextState;
}

//
// ---> handleEvent(IcmpSelfEvent &event);
//
// handle IcmpSelfEvent from LinkProber
//
LinkProberState* WaitState::handleEvent(IcmpSelfEvent &event)
{
    MUXLOGDEBUG(getMuxPortConfig().getPortName());

    LinkProberStateMachine *stateMachine = dynamic_cast<LinkProberStateMachine *> (getStateMachine());
    LinkProberState *nextState;

    mPeerEventCount = 0;
    if (++mSelfEventCount >= getMuxPortConfig().getPositiveStateChangeRetryCount()) {
        nextState = dynamic_cast<LinkProberState *> (stateMachine->getActiveState());
    }
    else {
        nextState = dynamic_cast<LinkProberState *> (stateMachine->getWaitState());
    }

    return nextState;
}

//
// ---> handleEvent(IcmpUnknownEvent &event);
//
// handle IcmpUnknownEvent from LinkProber
//
LinkProberState* WaitState::handleEvent(IcmpUnknownEvent &event)
{
    MUXLOGDEBUG(getMuxPortConfig().getPortName());

    LinkProberStateMachine *stateMachine = dynamic_cast<LinkProberStateMachine *> (getStateMachine());
    LinkProberState *nextState = dynamic_cast<LinkProberState *> (stateMachine->getWaitState());

    resetState();

    return nextState;
}

//
// ---> resetState();
//
// reset current state attributes
//
void WaitState::resetState()
{
    MUXLOGDEBUG(getMuxPortConfig().getPortName());

    mSelfEventCount = 0;
    mPeerEventCount = 0;
}

} /* namespace link_prober */
