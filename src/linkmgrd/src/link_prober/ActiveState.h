/*
 * ActiveState.h
 *
 *  Created on: Oct 7, 2020
 *      Author: tamer
 */

#ifndef LINK_PROBER_ACTIVESTATE_H_
#define LINK_PROBER_ACTIVESTATE_H_

#include "LinkProberState.h"

namespace link_prober
{
class LinkProberStateMachine;

/**
 *@class ActiveState
 *
 *@brief maintains Active state of LinkProber
 */
class ActiveState: public LinkProberState
{
public:
    /**
    *@method ActiveState
    *
    *@brief class default constructor
    */
    ActiveState() = delete;

    /**
    *@method ActiveState
    *
    *@brief class copy constructor
    *
    *@param ActiveState (in)  reference to ActiveState object to be copied
    */
    ActiveState(const ActiveState &) = delete;

    /**
    *@method ActiveState
    *
    *@brief class constructor
    *
    *@param stateMachine (in)   reference to LinkProberStateMachine
    *@param muxPortConfig (in)  reference to MuxPortConfig object
    */
    ActiveState(
        LinkProberStateMachine &stateMachine,
        common::MuxPortConfig &muxPortConfig
    );

    /**
    *@method ~ActiveState
    *
    *@brief class destructor
    */
    virtual ~ActiveState() = default;

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
    *@return LinkProberState Active label
    */
    virtual LinkProberState::Label getStateLabel() override {return LinkProberState::Label::Active;};

private:
    uint8_t mPeerEventCount = 0;
    uint8_t mUnknownEventCount = 0;
};

} /* namespace link_prober */

#endif /* LINK_PROBER_ACTIVESTATE_H_ */
