/*
 * UnknownState.h
 *
 *  Created on: Oct 7, 2020
 *      Author: tamer
 */

#ifndef LINK_PROBER_UNKNOWNSTATE_H_
#define LINK_PROBER_UNKNOWNSTATE_H_

#include <stdint.h>

#include "LinkProberState.h"

namespace link_prober
{
class LinkProberStateMachine;

/**
 *@class UnknownState
 *
 *@brief maintains Unknown state of LinkProber
 */
class UnknownState : public LinkProberState
{
public:
    /**
    *@method UnknownState
    *
    *@brief class default constructor
    */
    UnknownState() = delete;

    /**
    *@method UnknownState
    *
    *@brief class copy constructor
    *
    *@param UnknownState (in)  reference to UnknownState object to be copied
    */
    UnknownState(const UnknownState &) = delete;

    /**
    *@method UnknownState
    *
    *@brief class constructor
    *
    *@param stateMachine (in)   reference to LinkProberStateMachine
    *@param muxPortConfig (in)  reference to MuxPortConfig object
    */
    UnknownState(
        LinkProberStateMachine &stateMachine,
        common::MuxPortConfig &muxPortConfig
    );

    /**
    *@method ~UnknownState
    *
    *@brief class destructor
    */
    virtual ~UnknownState() = default;

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
    *@return LinkProberState Unknown label
    */
    virtual LinkProberState::Label getStateLabel() override {return LinkProberState::Label::Unknown;};

private:
    uint8_t mSelfEventCount = 0;
    uint8_t mPeerEventCount = 0;
};

} /* namespace link_prober */

#endif /* LINK_PROBER_UNKNOWNSTATE_H_ */
