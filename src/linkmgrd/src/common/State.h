/*
 * State.h
 *
 *  Created on: Oct 7, 2020
 *      Author: tamer
 */

#ifndef STATE_H_
#define STATE_H_

#include <memory>
#include "common/MuxPortConfig.h"

namespace common
{
class StateMachine;

/**
 *@class State
 *
 *@brief Maintains common state functionality
 */
class State
{
public:
    /**
    *@method State
    *
    *@brief class default constructor
    */
    State() = delete;

    /**
    *@method State
    *
    *@brief class copy constructor
    *
    *@param State (in)  reference to State object to be copied
    */
    State(const State &) = delete;

    /**
    *@method State
    *
    *@brief class constructor
    *
    *@param stateMachine (in)   reference to StateMachine object
    *@param muxPortConfig (in)  reference to MuxPortConfig object
    */
    State(
        StateMachine &stateMachine,
        MuxPortConfig &muxPortConfig
    );

    /**
    *@method ~State
    *
    *@brief class destructor
    */
    virtual ~State() = default;

    /**
    *@method getStateMachine
    *
    *@brief getter for StateMachine object
    *
    *@return StateMacine object
    */
    StateMachine* getStateMachine() {return &mStateMachine;};

    /**
    *@method getMuxPortConfig
    *
    *@brief getter for MuxPortConfig object
    *
    *@return MuxPortConfig object
    */
    const MuxPortConfig& getMuxPortConfig() const {return mMuxPortConfig;};

    /**
    *@method resetState
    *
    *@brief reset current state attributes. It is called when transitioning into State.
    *
    *@param address (in) server IPv4 address
    *
    *@return none
    */
    virtual void resetState() = 0;

private:
    StateMachine &mStateMachine;
    MuxPortConfig &mMuxPortConfig;
};

} /* namespace common */

#endif /* STATE_H_ */
