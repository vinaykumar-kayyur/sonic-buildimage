/*
 * LinkState.cpp
 *
 *  Created on: Oct 18, 2020
 *      Author: tamer
 */

#include <link_state/LinkState.h>
#include <link_state/LinkStateMachine.h>

namespace link_state
{

//
// ---> LinkState(LinkStateMachine &stateMachine, common::MuxPortConfig &muxPortConfig);
//
// class constructor
//
LinkState::LinkState(
    LinkStateMachine &stateMachine,
    common::MuxPortConfig &muxPortConfig
) :
    common::State(
        *dynamic_cast<common::StateMachine *> (&stateMachine),
        muxPortConfig
    )
{
}

} /* namespace link_state */
