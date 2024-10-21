#ifndef _WB_FAN_DRIVER_H_
#define _WB_FAN_DRIVER_H_

/**
 * dfd_get_fan_status_str - Obtaining fan status
 * @index: Number of the fan, starting from 1
 * return: Success: Length of the status string
 *       : Negative value - Read failed
 */
ssize_t dfd_get_fan_status_str(unsigned int fan_index, char *buf, size_t count);

/**
 * dfd_get_fan_info - Obtaining Fan Information
 * @index: Number of the fan, starting from 1
 * @cmd: Fan information type, fan name :2, fan serial number :3, fan hardware version :5
 * @buf: Receive buf
 * @count: Accept the buf length
 * return: Success: Returns the length of buf
 *       : Failed: A negative value is returned
 */
ssize_t dfd_get_fan_info(unsigned int fan_index, uint8_t cmd, char *buf, size_t count);

/**
 * dfd_get_fan_speed - Obtain the fan speed
 * @fan_index: Number of the fan, starting from 1
 * @motor_index: Motor number, starting with 1
 * @speed: Speed value
 * return: Success :0
 *       : Failed: A negative value is returned
 */
int dfd_get_fan_speed(unsigned int fan_index, unsigned int motor_index,unsigned int *speed);

/**
 * dfd_get_fan_speed_str - Obtain the fan speed
 * @fan_index: Number of the fan, starting from 1
 * @motor_index: Motor number, starting with 1
 * @buf: Receive buf
 * @count: Receive buf length
 * return: Success :0
 *       : Failed: A negative value is returned
 */
ssize_t dfd_get_fan_speed_str(unsigned int fan_index, unsigned int motor_index,
            char *buf, size_t count);

/**
 * dfd_set_fan_pwm - Set the fan speed duty cycle
 * @fan_index: Number of the fan, starting from 1
 * @pwm:   Duty cycle
 * return: Success :0
 *       : Failed: A negative value is returned
 */
int dfd_set_fan_pwm(unsigned int fan_index, int pwm);

/**
 * dfd_get_fan_pwm - Obtain the fan speed duty cycle
 * @fan_index: Number of the fan, starting from 1
 * @pwm:  Duty cycle
 * return: Success :0
 *       : Failed: A negative value is returned
 */
int dfd_get_fan_pwm(unsigned int fan_index, int *pwm);

/**
 * dfd_get_fan_pwm_str - Obtain the fan speed duty cycle
 * @fan_index: Number of the fan, starting from 1
 * @buf: Receive buf
 * @count: Receive buf length
 * return: Success :0
 *       : Failed: A negative value is returned
 */
ssize_t dfd_get_fan_pwm_str(unsigned int fan_index, char *buf, size_t count);

/**
 * dfd_get_fan_motor_speed_tolerance_str - Obtain the fan speed tolerance
 * @fan_index: Number of the fan, starting from 1
 * @motor_index: Motor number, starting with 1
 * @buf: Receive buf
 * @count: Receive buf length
 * return: Success :0
 *       : Failed: A negative value is returned
 */
ssize_t dfd_get_fan_motor_speed_tolerance_str(unsigned int fan_index, unsigned int motor_index,
            char *buf, size_t count);

/**
 * dfd_get_fan_speed_target - Obtain the standard fan speed
 * @fan_index
 * @motor_index
 * @value Standard speed value
 * @returns: Success :0
 *         : Failed: A negative value is returned
 */
int dfd_get_fan_speed_target(unsigned int fan_index, unsigned int motor_index, int *value);

/**
 * dfd_get_fan_motor_speed_target_str - Obtain the standard fan speed
 * @fan_index: Number of the fan, starting from 1
 * @motor_index: Motor number, starting with 1
 * @buf: Receive buf
 * @count: Receive buf length
 * return: Success :0
 *       : Failed: A negative value is returned
 */
ssize_t dfd_get_fan_motor_speed_target_str(unsigned int fan_index, unsigned int motor_index,
            char *buf, size_t count);

/**
 * dfd_get_fan_direction_str - Obtain the fan air duct type
 * @fan_index: Number of the fan, starting from 1
 * @buf :Duct type receives buf
 * @count :Duct type receives buf length
 * @returns: Succeeded: Air duct type String length
 *           Failed: A negative value is returned
 */
ssize_t dfd_get_fan_direction_str(unsigned int fan_index, char *buf, size_t count);

/**
 * dfd_get_fan_motor_speed_max_str - Obtain the standard fan speed
 * @fan_index: Number of the fan, starting from 1
 * @motor_index: Motor number, starting with 1
 * @buf: Receive buff
 * @count: Receive buf length
 * return: Success :0
 *       :Failed: A negative value is returned
 */
ssize_t dfd_get_fan_motor_speed_max_str(unsigned int fan_index, unsigned int motor_index,
            char *buf, size_t count);

/**
 * dfd_get_fan_motor_speed_min_str - Obtain the standard fan speed
 * @fan_index: Number of the fan, starting from 1
 * @motor_index: Motor number, starting with 1
 * @buf: Receive buf
 * @count: Receive buf length
 * return: Success :0
 *       : Failed: A negative value is returned
 */
ssize_t dfd_get_fan_motor_speed_min_str(unsigned int fan_index, unsigned int motor_index,
            char *buf, size_t count);

#endif /* _WB_FAN_DRIVER_H_ */
