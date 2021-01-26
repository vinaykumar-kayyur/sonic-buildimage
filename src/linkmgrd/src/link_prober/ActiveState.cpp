/*
 * ActiveState.cpp
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
// ---> ActiveState(LinkProberStateMachine &stateMachine, common::MuxPortConfig &muxPortConfig);
//
// class constructor
//
ActiveState::ActiveState(
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
LinkProberState* ActiveState::handleEvent(IcmpPeerEvent &event)
{
    MUXLOGDEBUG(getMuxPortConfig().getPortName());

    LinkProberStateMachine *stateMachine = dynamic_cast<LinkProberStateMachine *> (getStateMachine());
    LinkProberState *nextState;

    mUnknownEventCount = 0;
    if (++mPeerEventCount >= getMuxPortConfig().getStateChangeRetryCount()) {
        nextState = dynamic_cast<LinkProberState *> (stateMachine->getStandbyState());
    }
    else {
        nextState = dynamic_cast<LinkProberState *> (stateMachine->getActiveState());
    }

    return nextState;
}

//
// ---> handleEvent(IcmpSelfEvent &event);
//
// handle IcmpSelfEvent from LinkProber
//
LinkProberState* ActiveState::handleEvent(IcmpSelfEvent &event)
{
    MUXLOGDEBUG(getMuxPortConfig().getPortName());

    LinkProberStateMachine *stateMachine = dynamic_cast<LinkProberStateMachine *> (getStateMachine());
    LinkProberState *nextState = dynamic_cast<LinkProberState *> (stateMachine->getActiveState());

    resetState();

    return nextState;
}

//
// ---> handleEvent(IcmpUnknownEvent &event);
//
// handle IcmpUnknownEvent from LinkProber
//
LinkProberState* ActiveState::handleEvent(IcmpUnknownEvent &event)
{
    MUXLOGDEBUG(getMuxPortConfig().getPortName());

    LinkProberStateMachine *stateMachine = dynamic_cast<LinkProberStateMachine *> (getStateMachine());
    LinkProberState *nextState;

    mPeerEventCount = 0;
    if (++mUnknownEventCount >= getMuxPortConfig().getStateChangeRetryCount()) {
        nextState = dynamic_cast<LinkProberState *> (stateMachine->getUnknownState());
    }
    else {
        nextState = dynamic_cast<LinkProberState *> (stateMachine->getActiveState());
    }

    return nextState;
}

//
// ---> resetState();
//
// reset current state attributes
//
void ActiveState::resetState()
{
    MUXLOGDEBUG(getMuxPortConfig().getPortName());

    mPeerEventCount = 0;
    mUnknownEventCount = 0;
}

} /* namespace link_prober */
