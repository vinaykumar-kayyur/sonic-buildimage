/*
 * FailedState.cpp
 *
 *  Created on: Oct 20, 2020
 *      Author: tamer
 */

#include "UnknownState.h"

#include "mux_state/ActiveState.h"
#include "mux_state/StandbyState.h"
#include "mux_state/MuxStateMachine.h"

#include "common/MuxLogger.h"

namespace mux_state
{

//
// ---> UnknownState(MuxStateMachine &stateMachine, common::MuxPortConfig &muxPortConfig);
//
// class constructor
//
UnknownState::UnknownState(
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
MuxState* UnknownState::handleEvent(ActiveEvent &event)
{
    MUXLOGDEBUG(getMuxPortConfig().getPortName());

    MuxStateMachine *stateMachine = dynamic_cast<MuxStateMachine *> (getStateMachine());
    MuxState *nextState;

    mStandbyEventCount = 0;
    mErrorEventCount = 0;
    if (++mActiveEventCount >= getMuxPortConfig().getMuxStateChangeRetryCount()) {
        nextState = dynamic_cast<MuxState *> (stateMachine->getActiveState());
    }
    else {
        nextState = dynamic_cast<MuxState *> (stateMachine->getUnknownState());
    }

    return nextState;
}

//
// ---> handleEvent(StandbyEvent &event);
//
// handle StandbyEvent from state db/xcvrd
//
MuxState* UnknownState::handleEvent(StandbyEvent &event)
{
    MUXLOGDEBUG(getMuxPortConfig().getPortName());

    MuxStateMachine *stateMachine = dynamic_cast<MuxStateMachine *> (getStateMachine());
    MuxState *nextState;

    mActiveEventCount = 0;
    mErrorEventCount = 0;
    if (++mStandbyEventCount >= getMuxPortConfig().getMuxStateChangeRetryCount()) {
        nextState = dynamic_cast<MuxState *> (stateMachine->getStandbyState());
    }
    else {
        nextState = dynamic_cast<MuxState *> (stateMachine->getUnknownState());
    }

    return nextState;
}

//
// ---> handleEvent(UnknownEvent &event);
//
// handle UnknownEvent from state db/xcvrd
//
MuxState* UnknownState::handleEvent(UnknownEvent &event)
{
    MUXLOGDEBUG(getMuxPortConfig().getPortName());

    MuxStateMachine *stateMachine =
        dynamic_cast<MuxStateMachine *> (getStateMachine());
    MuxState *nextState =
        dynamic_cast<MuxState *> (stateMachine->getUnknownState());

    resetState();

    return nextState;
}

//
// ---> handleEvent(ErrorEvent &event);
//
// handle ErrorEvent from state db
//
MuxState* UnknownState::handleEvent(ErrorEvent &event)
{
    MUXLOGDEBUG(getMuxPortConfig().getPortName());

    MuxStateMachine *stateMachine =
        dynamic_cast<MuxStateMachine *> (getStateMachine());
    MuxState *nextState;

    mActiveEventCount = 0;
    mStandbyEventCount = 0;
    if (++mErrorEventCount >= getMuxPortConfig().getMuxStateChangeRetryCount()) {
        nextState = dynamic_cast<MuxState *> (stateMachine->getErrorState());
    }
    else {
        nextState = dynamic_cast<MuxState *> (stateMachine->getUnknownState());
    }

    return nextState;
}

//
// ---> resetState()
//
// reset current state attributes
//
void UnknownState::resetState()
{
    MUXLOGDEBUG(getMuxPortConfig().getPortName());

    mActiveEventCount = 0;
    mStandbyEventCount = 0;
    mErrorEventCount = 0;
}

} /* namespace mux_state */
