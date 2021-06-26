/*
 * LinkStateMachine.cpp
 *
 *  Created on: Oct 20, 2020
 *      Author: tamer
 */

#include <boost/bind/bind.hpp>

#include "common/MuxLogger.h"
#include "link_state/LinkStateMachine.h"
#include "link_manager/LinkManagerStateMachine.h"


namespace link_state
{
//
// static members
//
UpEvent LinkStateMachine::mUpEvent;
DownEvent LinkStateMachine::mDownEvent;

//
// ---> LinkStateMachine(
//          link_manager::LinkManagerStateMachine &linkManagerStateMachine,
//          boost::asio::io_service::strand &strand,
//          common::MuxPortConfig &muxPortConfig,
//          LinkState::Label label
//      );
//
// class constructor
//
LinkStateMachine::LinkStateMachine(
    link_manager::LinkManagerStateMachine &linkManagerStateMachine,
    boost::asio::io_service::strand &strand,
    common::MuxPortConfig &muxPortConfig,
    LinkState::Label label
) :
    common::StateMachine(strand, muxPortConfig),
    mLinkManagerStateMachine(linkManagerStateMachine),
    mUpState(*this, muxPortConfig),
    mDownState(*this, muxPortConfig)
{
    enterState(label);
}

//
// ---> enterState(LinkState::Label label);
//
// force the state machine to enter a given state
//
void LinkStateMachine::enterState(LinkState::Label label)
{
    MUXLOGDEBUG(getMuxPortConfig().getPortName());
    switch (label) {
    case LinkState::Label::Up:
        setCurrentState(dynamic_cast<UpState *> (getUpState()));
        break;
    case LinkState::Label::Down:
        setCurrentState(dynamic_cast<DownState *> (getDownState()));
        break;
    default:
        break;
    }
}

//
// ---> postLinkManagerEvent(LinkState* linkState);
//
// post LinkState change event to LinkManager state machine
//
inline
void LinkStateMachine::postLinkManagerEvent(LinkState* linkState)
{
    boost::asio::io_service::strand &strand = mLinkManagerStateMachine.getStrand();
    boost::asio::io_service &ioService = strand.context();
    ioService.post(strand.wrap(boost::bind(
        static_cast<void (link_manager::LinkManagerStateMachine::*) (link_manager::LinkStateEvent&, LinkState::Label)>
            (&link_manager::LinkManagerStateMachine::handleStateChange),
        &mLinkManagerStateMachine,
        link_manager::LinkManagerStateMachine::getLinkStateEvent(),
        linkState->getStateLabel()
    )));
}

//
// ---> LinkStateMachine::postLinkStateEvent(E &e);
//
// post LinkState event to the state machine
//
template <class E>
void LinkStateMachine::postLinkStateEvent(E &e)
{
    boost::asio::io_service::strand &strand = getStrand();
    boost::asio::io_service &ioService = strand.context();
    ioService.post(strand.wrap(boost::bind(
        static_cast<void (LinkStateMachine::*) (decltype(e))>
            (&LinkStateMachine::processEvent),
        this,
        e
    )));
}

//
// ---> postLinkStateEvent<UpEvent>(UpEvent &e);
//
// post LinkState event to the state machine
//
template
void LinkStateMachine::postLinkStateEvent<UpEvent>(UpEvent &e);

//
// ---> postLinkStateEvent<DownEvent>(DownEvent &e);
//
// post LinkState event to the state machine
//
template
void LinkStateMachine::postLinkStateEvent<DownEvent>(DownEvent &e);

//
// ---> processEvent(T &t);
//
// process LinkState event
//
template <typename T>
void LinkStateMachine::processEvent(T &t)
{
    LinkState *currentLinkState = dynamic_cast<LinkState *> (getCurrentState());
    LinkState *nextLinkState = currentLinkState->handleEvent(t);
    if (nextLinkState != currentLinkState) {
        postLinkManagerEvent(nextLinkState);
    }
    setCurrentState(nextLinkState);
}

//
// ---> processEvent<UpEvent&>(UpEvent &event);
//
// process LinkState event
//
template
void LinkStateMachine::processEvent<UpEvent&>(UpEvent &event);

//
// ---> processEvent<DownEvent&>(DownEvent &event);
//
// process LinkState event
//
template
void LinkStateMachine::processEvent<DownEvent&>(DownEvent &event);

} /* namespace link_state */
