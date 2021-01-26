/*
 * DownState.cpp
 *
 *  Created on: Oct 20, 2020
 *      Author: tamer
 */

#include "common/MuxLogger.h"
#include "link_state/DownState.h"
#include "link_state/UpState.h"
#include "link_state/LinkStateMachine.h"

namespace link_state
{

//
// ---> DownState(LinkStateMachine &stateMachine, common::MuxPortConfig &muxPortConfig);
//
// class constructor
//
DownState::DownState(
    LinkStateMachine &stateMachine,
    common::MuxPortConfig &muxPortConfig
) :
    LinkState(stateMachine, muxPortConfig)
{
}

//
// ---> handleEvent(UpEvent &event);
//
// handle UpEvent from state db
//
LinkState* DownState::handleEvent(UpEvent &event)
{
    MUXLOGDEBUG(getMuxPortConfig().getPortName());

    LinkStateMachine *stateMachine = dynamic_cast<LinkStateMachine *> (getStateMachine());
    LinkState *nextState;

    if (++mUpEventCount >= getMuxPortConfig().getLinkStateChangeRetryCount()) {
        nextState = dynamic_cast<LinkState *> (stateMachine->getUpState());
    }
    else {
        nextState = dynamic_cast<LinkState *> (stateMachine->getDownState());
    }

    return nextState;
}

//
// ---> handleEvent(DownEvent &event);
//
// handle DownEvent from state db
//
LinkState* DownState::handleEvent(DownEvent &event)
{
    MUXLOGDEBUG(getMuxPortConfig().getPortName());

    LinkStateMachine *stateMachine = dynamic_cast<LinkStateMachine *> (getStateMachine());
    LinkState *nextState = dynamic_cast<LinkState *> (stateMachine->getDownState());

    resetState();

    return nextState;
}

//
// ---> resetState();
//
// reset current state attributes
//
void DownState::resetState()
{
    MUXLOGDEBUG(getMuxPortConfig().getPortName());
    mUpEventCount = 0;
}

} /* namespace link_state */
