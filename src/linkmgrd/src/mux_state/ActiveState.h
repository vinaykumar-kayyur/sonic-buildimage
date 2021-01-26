/*
 * ActiveState.h
 *
 *  Created on: Oct 20, 2020
 *      Author: tamer
 */

#ifndef MUX_STATE_ACTIVESTATE_H_
#define MUX_STATE_ACTIVESTATE_H_

#include <mux_state/MuxState.h>

namespace mux_state
{

/**
 *@class ActiveState
 *
 *@brief maintains ActiveState state of MuxState
 */
class ActiveState: public MuxState
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
    *@method DownState
    *
    *@brief class constructor
    *
    *@param stateMachine (in)   reference to LinkStateMachine
    *@param muxPortConfig (in)  reference to MuxPortConfig object
    */
    ActiveState(
        MuxStateMachine &stateMachine,
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
    *@return MuxState Active label
    */
    virtual MuxState::Label getStateLabel() override {return MuxState::Label::Active;};

private:
    uint8_t mStandbyEventCount = 0;
    uint8_t mUnknownEventCount = 0;
};

} /* namespace mux_state */

#endif /* MUX_STATE_ACTIVESTATE_H_ */
