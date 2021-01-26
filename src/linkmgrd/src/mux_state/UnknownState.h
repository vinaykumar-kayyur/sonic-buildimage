/*
 * UnknownState.h
 *
 *  Created on: Oct 20, 2020
 *      Author: tamer
 */

#ifndef MUX_STATE_UNKNOWNSTATE_H_
#define MUX_STATE_UNKNOWNSTATE_H_

#include <mux_state/MuxState.h>

namespace mux_state
{

/**
 *@class UnknownState
 *
 *@brief maintains UnknownState state of MuxState
 */
class UnknownState: public MuxState
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
    *@param stateMachine (in)   reference to LinkStateMachine
    *@param muxPortConfig (in)  reference to MuxPortConfig object
    */
    UnknownState(
        MuxStateMachine &stateMachine,
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
    *@brief handle ActiveEvent from state db/xcvrd
    *
    *@param event (in)  reference to ActiveEvent
    *
    *@return pointer to next MuxState
    */
    virtual MuxState* handleEvent(ActiveEvent &event) override;

    /**
    *@method handleEvent
    *
    *@brief handle StandbyEvent from state db/xcvrd
    *
    *@param event (in)  reference to StandbyEvent
    *
    *@return pointer to next MuxState
    */
    virtual MuxState* handleEvent(StandbyEvent &event) override;

    /**
    *@method handleEvent
    *
    *@brief handle UnknownEvent from state db/xcvrd
    *
    *@param event (in)  reference to UnknownEvent
    *
    *@return pointer to next MuxState
    */
    virtual MuxState* handleEvent(UnknownEvent &event) override;

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
    *@brief getter for MuxState label
    *
    *@return MuxState Unknown label
    */
    virtual MuxState::Label getStateLabel() override {return MuxState::Label::Unknown;};

private:
    uint8_t mActiveEventCount = 0;
    uint8_t mStandbyEventCount = 0;
};

} /* namespace mux_state */

#endif /* MUX_STATE_UNKNOWNSTATE_H_ */
