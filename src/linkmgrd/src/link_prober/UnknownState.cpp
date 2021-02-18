/*
 * UnknownState.cpp
 *
 *  Created on: Oct 7, 2020
 *      Author: tamer
 */

#include "link_prober/ActiveState.h"
#include "link_prober/StandbyState.h"
#include "link_prober/UnknownState.h"
#include "link_prober/LinkProberStateMachine.h"

#include "common/MuxLogger.h"

namespace link_prober
{

//
// ---> UnknownState(LinkProberStateMachine &stateMachine, common::MuxPortConfig &muxPortConfig);
//
// class constructor
//
UnknownState::UnknownState(
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
LinkProberState* UnknownState::handleEvent(IcmpPeerEvent &event)
{
    MUXLOGDEBUG(getMuxPortConfig().getPortName());

    LinkProberStateMachine *stateMachine =
        dynamic_cast<LinkProberStateMachine *> (getStateMachine());
    LinkProberState *nextState;

    mSelfEventCount = 0;
    if (++mPeerEventCount >= getMuxPortConfig().getPositiveStateChangeRetryCount()) {
        nextState = dynamic_cast<LinkProberState *> (stateMachine->getStandbyState());
    }
    else {
        nextState = dynamic_cast<LinkProberState *> (stateMachine->getUnknownState());
    }

    return nextState;
}

//
// ---> handleEvent(IcmpSelfEvent &event);
//
// handle IcmpSelfEvent from LinkProber
//
LinkProberState* UnknownState::handleEvent(IcmpSelfEvent &event)
{
    MUXLOGDEBUG(getMuxPortConfig().getPortName());

    LinkProberStateMachine *stateMachine =
        dynamic_cast<LinkProberStateMachine *> (getStateMachine());
    LinkProberState *nextState;

    mPeerEventCount = 0;
    if (++mSelfEventCount >= getMuxPortConfig().getPositiveStateChangeRetryCount()) {
        nextState = dynamic_cast<LinkProberState *> (stateMachine->getActiveState());
    }
    else {
        nextState = dynamic_cast<LinkProberState *> (stateMachine->getUnknownState());
    }

    return nextState;
}

//
// ---> handleEvent(IcmpUnknownEvent &event);
//
// handle IcmpUnknownEvent from LinkProber
//
LinkProberState* UnknownState::handleEvent(IcmpUnknownEvent &event)
{
    MUXLOGDEBUG(getMuxPortConfig().getPortName());

    LinkProberStateMachine *stateMachine = dynamic_cast<LinkProberStateMachine *> (getStateMachine());
    LinkProberState *nextState = dynamic_cast<LinkProberState *> (stateMachine->getUnknownState());

    resetState();

    return nextState;
}

//
// ---> resetState();
//
// reset current state attributes
//
void UnknownState::resetState()
{
    MUXLOGDEBUG(getMuxPortConfig().getPortName());

    mSelfEventCount = 0;
    mPeerEventCount = 0;
}

} /* namespace link_prober */
