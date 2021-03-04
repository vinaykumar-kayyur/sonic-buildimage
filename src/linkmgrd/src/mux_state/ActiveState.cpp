/*
 * ActiveState.cpp
 *
 *  Created on: Oct 20, 2020
 *      Author: tamer
 */

#include "mux_state/ActiveState.h"
#include "mux_state/StandbyState.h"
#include "mux_state/MuxStateMachine.h"

#include "common/MuxLogger.h"
#include "UnknownState.h"

namespace mux_state
{

//
// ---> ActiveState(MuxStateMachine &stateMachine, common::MuxPortConfig &muxPortConfig);
//
// class constructor
//
ActiveState::ActiveState(
    MuxStateMachine &stateMachine,
    common::MuxPortConfig &muxPortConfig
) :
    MuxState(stateMachine, muxPortConfig)
{
}

//
// ---> handleEvent(ActiveEvent &event);
//
// handle ActiveEvent from state db/xcvrd
//
MuxState* ActiveState::handleEvent(ActiveEvent &event)
{
    MUXLOGDEBUG(getMuxPortConfig().getPortName());

    MuxStateMachine *stateMachine = dynamic_cast<MuxStateMachine *> (getStateMachine());
    MuxState *nextState =
        dynamic_cast<MuxState *> (stateMachine->getActiveState());

    resetState();

    return nextState;
}

//
// ---> handleEvent(StandbyEvent &event);
//
// handle StandbyEvent from state db/xcvrd
//
MuxState* ActiveState::handleEvent(StandbyEvent &event)
{
    MUXLOGDEBUG(getMuxPortConfig().getPortName());

    MuxStateMachine *stateMachine = dynamic_cast<MuxStateMachine *> (getStateMachine());
    MuxState *nextState;

    mUnknownEventCount = 0;
    mErrorEventCount = 0;
    if (++mStandbyEventCount >= getMuxPortConfig().getMuxStateChangeRetryCount()) {
        nextState = dynamic_cast<MuxState *> (stateMachine->getStandbyState());
    }
    else {
        nextState = dynamic_cast<MuxState *> (stateMachine->getActiveState());
    }

    return nextState;
}

//
// ---> handleEvent(UnknownEvent &event);
//
// handle UnknownEvent from state db/xcvrd
//
MuxState* ActiveState::handleEvent(UnknownEvent &event)
{
    MUXLOGDEBUG(getMuxPortConfig().getPortName());

    MuxStateMachine *stateMachine = dynamic_cast<MuxStateMachine *> (getStateMachine());
    MuxState *nextState;

    mStandbyEventCount = 0;
    mErrorEventCount = 0;
    if (++mUnknownEventCount >= getMuxPortConfig().getMuxStateChangeRetryCount()) {
        nextState = dynamic_cast<MuxState *> (stateMachine->getUnknownState());
    }
    else {
        nextState = dynamic_cast<MuxState *> (stateMachine->getActiveState());
    }

    return nextState;
}

//
// ---> handleEvent(ErrorEvent &event);
//
// handle ErrorEvent from state db
//
MuxState* ActiveState::handleEvent(ErrorEvent &event)
{
    MUXLOGDEBUG(getMuxPortConfig().getPortName());

    MuxStateMachine *stateMachine =
        dynamic_cast<MuxStateMachine *> (getStateMachine());
    MuxState *nextState;

    mStandbyEventCount = 0;
    mUnknownEventCount = 0;
    if (++mErrorEventCount >= getMuxPortConfig().getMuxStateChangeRetryCount()) {
        nextState = dynamic_cast<MuxState *> (stateMachine->getErrorState());
    }
    else {
        nextState = dynamic_cast<MuxState *> (stateMachine->getActiveState());
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

    mStandbyEventCount = 0;
    mUnknownEventCount = 0;
    mErrorEventCount = 0;
}

} /* namespace mux_state */
