/*
 * LinkState.h
 *
 *  Created on: Oct 18, 2020
 *      Author: tamer
 */

#ifndef LINK_STATE_LINKSTATE_H_
#define LINK_STATE_LINKSTATE_H_

#include <common/State.h>

namespace link_state
{
class LinkStateMachine;
class UpEvent;
class DownEvent;

/**
 *@class LinkState
 *
 *@brief base class for different LinkState states
 */
class LinkState: public common::State
{
public:
    /**
     *@enum Label
     *
     *@brief Label corresponding to each LinkState State
     */
    enum Label {
        Up,
        Down,

        Count
    };

public:
    /**
    *@method LinkState
    *
    *@brief class default constructor
    */
    LinkState() = delete;

    /**
    *@method LinkState
    *
    *@brief class copy constructor
    *
    *@param LinkState (in)  reference to LinkState object to be copied
    */
    LinkState(const LinkState &) = delete;

    /**
    *@method LinkState
    *
    *@brief class constructor
    *
    *@param stateMachine (in)   reference to LinkProberStateMachine object
    *@param muxPortConfig (in)  reference to MuxPortConfig object
    */
    LinkState(
        LinkStateMachine &stateMachine,
        common::MuxPortConfig &muxPortConfig
    );

    /**
    *@method ~LinkProber
    *
    *@brief class destructor
    */
    virtual ~LinkState() = default;

    /**
    *@method handleEvent
    *
    *@brief handle UpEvent from state db
    *
    *@param event (in)  reference to UpEvent
    *
    *@return pointer to next LinkState
    */
    virtual LinkState* handleEvent(UpEvent &event) = 0;

    /**
    *@method handleEvent
    *
    *@brief handle DownEvent from state db
    *
    *@param event (in)  reference to DownEvent
    *
    *@return pointer to next LinkState
    */
    virtual LinkState* handleEvent(DownEvent &event) = 0;

    /**
    *@method getStateLabel
    *
    *@brief getter for LinkState label
    *
    *@return LinkState Down label
    */
    virtual LinkState::Label getStateLabel() = 0;
};

} /* namespace link_state */

#endif /* LINK_STATE_LINKSTATE_H_ */
