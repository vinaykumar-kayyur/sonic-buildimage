/*
 * State.cpp
 *
 *  Created on: Oct 7, 2020
 *      Author: tamer
 */

#include <common/State.h>
#include "MuxLogger.h"

namespace common
{

//
// ---> State(StateMachine &stateMachine, MuxPortConfig &muxPortConfig);
//
// class constructor
//
State::State(
    StateMachine &stateMachine,
    MuxPortConfig &muxPortConfig
) :
    mStateMachine(stateMachine),
    mMuxPortConfig(muxPortConfig)
{
}

} /* namespace common */
