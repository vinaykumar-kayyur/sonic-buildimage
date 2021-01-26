/*
 * MuxState.cpp
 *
 *  Created on: Oct 18, 2020
 *      Author: tamer
 */

#include <mux_state/MuxState.h>
#include <mux_state/MuxStateMachine.h>

namespace mux_state
{

//
// ---> MuxState(MuxStateMachine &stateMachine, common::MuxPortConfig &muxPortConfig);
//
// class constructor
//
MuxState::MuxState(
    MuxStateMachine &stateMachine,
    common::MuxPortConfig &muxPortConfig
):
    common::State(
        *dynamic_cast<common::StateMachine *> (&stateMachine),
        muxPortConfig
    )
{
}

} /* namespace mux_state */
