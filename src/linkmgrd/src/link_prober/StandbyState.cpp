/*
 * StandbyState.cpp
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
// ---> StandbyState(LinkProberStateMachine &stateMachine, common::MuxPortConfig &muxPortConfig);
//
// class constructor
//
StandbyState::StandbyState(
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
LinkProberState* StandbyState::handleEvent(IcmpPeerEvent &event)
{
    MUXLOGDEBUG(getMuxPortConfig().getPortName());

    LinkProberStateMachine *stateMachine = dynamic_cast<LinkProberStateMachine *> (getStateMachine());
    LinkProberState *nextState =
        dynamic_cast<LinkProberState *> (stateMachine->getStandbyState());

    resetState();

    return nextState;
}

//
// ---> handleEvent(IcmpSelfEvent &event);
//
// handle IcmpSelfEvent from LinkProber
//
LinkProberState* StandbyState::handleEvent(IcmpSelfEvent &event)
{
    MUXLOGDEBUG(getMuxPortConfig().getPortName());

    LinkProberStateMachine *stateMachine = dynamic_cast<LinkProberStateMachine *> (getStateMachine());
    LinkProberState *nextState;

    mUnknownEventCount = 0;
    if (++mSelfEventCount >= getMuxPortConfig().getPositiveStateChangeRetryCount()) {
        nextState = dynamic_cast<LinkProberState *> (stateMachine->getActiveState());
    }
    else {
        nextState = dynamic_cast<LinkProberState *> (stateMachine->getStandbyState());
    }

    return nextState;
}

//
// ---> handleEvent(IcmpUnknownEvent &event);
//
// handle IcmpUnknownEvent from LinkProber
//
LinkProberState* StandbyState::handleEvent(IcmpUnknownEvent &event)
{
    MUXLOGDEBUG(getMuxPortConfig().getPortName());

    LinkProberStateMachine *stateMachine = dynamic_cast<LinkProberStateMachine *> (getStateMachine());
    LinkProberState *nextState;

    mSelfEventCount = 0;
    if (++mUnknownEventCount >= getMuxPortConfig().getNegativeStateChangeRetryCount()) {
        nextState = dynamic_cast<LinkProberState *> (stateMachine->getUnknownState());
    }
    else {
        nextState = dynamic_cast<LinkProberState *> (stateMachine->getStandbyState());
    }

    return nextState;
}

//
// ---> resetState();
//
// reset current state attributes
//
void StandbyState::resetState()
{
    MUXLOGDEBUG(getMuxPortConfig().getPortName());

    mSelfEventCount = 0;
    mUnknownEventCount = 0;
}

} /* namespace link_prober */
