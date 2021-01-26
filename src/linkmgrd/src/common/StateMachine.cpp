/*
 * StateMachine.cpp
 *
 *  Created on: Oct 4, 2020
 *      Author: tamer
 */

#include <common/State.h>
#include <common/StateMachine.h>
#include "MuxLogger.h"


namespace common
{

//
// ---> StateMachine(boost::asio::io_service::strand &strand, MuxPortConfig &muxPortConfig);
//
// class constructor
//
StateMachine::StateMachine(
    boost::asio::io_service::strand &strand,
    MuxPortConfig &muxPortConfig
) :
    mStrand(strand),
    mMuxPortConfig(muxPortConfig)
{
}

//
// ---> setCurrentState(common::State* state);
//
// setter for current state, reset state when changed
//
void StateMachine::setCurrentState(common::State* state)
{
    if (mCurrentState != state) {
        mCurrentState = state;
        mCurrentState->resetState();
    }
};

} /* namespace common */
