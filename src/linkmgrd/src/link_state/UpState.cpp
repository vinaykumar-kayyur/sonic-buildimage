/*
 * UpState.cpp
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
// ---> UpState(LinkStateMachine &stateMachine, common::MuxPortConfig &muxPortConfig);
//
// class constructor
//
UpState::UpState(
    LinkStateMachine &stateMachine,
    common::MuxPortConfig &muxPortConfig
) :
    LinkState(stateMachine, muxPortConfig)
{
}

//
// --->handleEvent(UpEvent &event);
//
// handle UpEvent from state db
//
LinkState* UpState::handleEvent(UpEvent &event)
{
    MUXLOGDEBUG(getMuxPortConfig().getPortName());

    LinkStateMachine *stateMachine = dynamic_cast<LinkStateMachine *> (getStateMachine());
    LinkState *nextState = dynamic_cast<LinkState *> (stateMachine->getUpState());

    resetState();

    return nextState;
}

//
// --->handleEvent(DownEvent &event);
//
// handle UpEvent from state db
//
LinkState* UpState::handleEvent(DownEvent &event)
{
    MUXLOGDEBUG(getMuxPortConfig().getPortName());

    LinkStateMachine *stateMachine = dynamic_cast<LinkStateMachine *> (getStateMachine());
    LinkState *nextState;

    if (++mDownEventCount >= getMuxPortConfig().getLinkStateChangeRetryCount()) {
        nextState = dynamic_cast<LinkState *> (stateMachine->getDownState());
    }
    else {
        nextState = dynamic_cast<LinkState *> (stateMachine->getUpState());
    }

    return nextState;
}

//
// --->resetState();
//
// reset current state attributes
//
void UpState::resetState()
{
    MUXLOGDEBUG(getMuxPortConfig().getPortName());
    mDownEventCount = 0;
}

} /* namespace link_state */
