/*
 * WaitState.h
 *
 *  Created on: Oct 18, 2020
 *      Author: tamer
 */

#ifndef LINK_PROBER_WAITSTATE_H_
#define LINK_PROBER_WAITSTATE_H_

#include <stdint.h>

#include "LinkProberState.h"

namespace link_prober
{
class LinkProberStateMachine;

/**
 *@class WaitState
 *
 *@brief maintains Wait state of LinkProber
 */
class WaitState : public LinkProberState
{
public:
    /**
    *@method WaitState
    *
    *@brief class default constructor
    */
    WaitState() = delete;

    /**
    *@method WaitState
    *
    *@brief class copy constructor
    *
    *@param WaitState (in)  reference to WaitState object to be copied
    */
    WaitState(const WaitState &) = delete;

    /**
    *@method WaitState
    *
    *@brief class constructor
    *
    *@param stateMachine (in)   reference to LinkProberStateMachine
    *@param muxPortConfig (in)  reference to MuxPortConfig object
    */
    WaitState(
        LinkProberStateMachine &stateMachine,
        common::MuxPortConfig &muxPortConfig
    );

    /**
    *@method ~WaitState
    *
    *@brief class destructor
    */
    virtual ~WaitState() = default;

    /**
    *@method handleEvent
    *
    *@brief handle IcmpPeerEvent from LinkProber
    *
    *@param event (in)  reference to IcmpPeerEvent
    *
    *@return pointer to next LinkProberState
    */
    virtual LinkProberState* handleEvent(IcmpPeerEvent &event) override;

    /**
    *@method handleEvent
    *
    *@brief handle IcmpSelfEvent from LinkProber
    *
    *@param event (in)  reference to IcmpSelfEvent
    *
    *@return pointer to next LinkProberState
    */
    virtual LinkProberState* handleEvent(IcmpSelfEvent &event) override;

    /**
    *@method handleEvent
    *
    *@brief handle IcmpUnknownEvent from LinkProber
    *
    *@param event (in)  reference to IcmpUnknownEvent
    *
    *@return pointer to next LinkProberState
    */
    virtual LinkProberState* handleEvent(IcmpUnknownEvent &event) override;

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
    *@brief getter for LinkeProberState label
    *
    *@return LinkProberState Wait label
    */
    virtual LinkProberState::Label getStateLabel() override {return LinkProberState::Label::Wait;};

private:
    uint8_t mSelfEventCount = 0;
    uint8_t mPeerEventCount = 0;
};

} /* namespace link_prober */

#endif /* LINK_PROBER_WAITSTATE_H_ */
