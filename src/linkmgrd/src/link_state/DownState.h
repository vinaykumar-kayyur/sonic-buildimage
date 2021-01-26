/*
 * DownState.h
 *
 *  Created on: Oct 20, 2020
 *      Author: tamer
 */

#ifndef LINK_STATE_DOWNSTATE_H_
#define LINK_STATE_DOWNSTATE_H_

#include <link_state/LinkState.h>

namespace link_state
{

/**
 *@class DownState
 *
 *@brief maintains DownState state of LinkState
 */
class DownState: public LinkState
{
public:
    /**
    *@method DownState
    *
    *@brief class default constructor
    */
    DownState() = delete;

    /**
    *@method DownState
    *
    *@brief class copy constructor
    *
    *@param DownState (in)  reference to DownState object to be copied
    */
    DownState(const DownState &) = delete;

    /**
    *@method DownState
    *
    *@brief class constructor
    *
    *@param stateMachine (in)   reference to LinkStateMachine
    *@param muxPortConfig (in)  reference to MuxPortConfig object
    */
    DownState(
        LinkStateMachine &stateMachine,
        common::MuxPortConfig &muxPortConfig
    );

    /**
    *@method ~DownState
    *
    *@brief class destructor
    */
    virtual ~DownState() = default;

    /**
    *@method handleEvent
    *
    *@brief handle UpEvent from state db
    *
    *@param event (in)  reference to UpEvent
    *
    *@return pointer to next LinkState
    */
    virtual LinkState* handleEvent(UpEvent &event) override;

    /**
    *@method handleEvent
    *
    *@brief handle DownEvent from state db
    *
    *@param event (in)  reference to DownEvent
    *
    *@return pointer to next LinkState
    */
    virtual LinkState* handleEvent(DownEvent &event) override;

    /**
    *@method resetState
    *
    *@brief reset current state attributes
    *
    *@return none
    */
    virtual void resetState() override;

    /**
    *@method getStateLabel
    *
    *@brief getter for LinkState label
    *
    *@return LinkState Down label
    */
    virtual LinkState::Label getStateLabel() override {return LinkState::Label::Down;};

private:
    uint8_t mUpEventCount = 0;
};

} /* namespace link_state */

#endif /* LINK_STATE_DOWNSTATE_H_ */
