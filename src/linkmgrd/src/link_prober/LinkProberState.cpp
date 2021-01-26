/*
 * LinkProberState.cpp
 *
 *  Created on: Oct 8, 2020
 *      Author: tamer
 */


#include <link_prober/LinkProberState.h>
#include <link_prober/LinkProberStateMachine.h>

namespace link_prober
{

//
// ---> LinkProberState(LinkProberStateMachine &stateMachine, common::MuxPortConfig &muxPortConfig);
//
// class constructor
//
LinkProberState::LinkProberState(
    LinkProberStateMachine &stateMachine,
    common::MuxPortConfig &muxPortConfig
) :
    common::State(
        *dynamic_cast<common::StateMachine *> (&stateMachine),
        muxPortConfig
    )
{
}

} /* namespace link_prober */
