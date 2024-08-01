#!/usr/bin/python3
# coding=utf8

import sys
sys.path.append('/home/pi/TurboPi/')
import time
import signal
import HiwonderSDK.mecanum as mecanum

if sys.version_info.major == 2:
    print('Please run this program with python3!')
    sys.exit(0)

chassis = mecanum.MecanumChassis()

start = True

def Stop(signum, frame):
    global start
    start = False
    print('Closing...')
    chassis.set_velocity(0, 0, 0)

signal.signal(signal.SIGINT, Stop)

def strafe_inches(inches):
    velocity = 50
    duration_per_inch = 0.25                                    
    print(f"Moving forward {inches} inches.")
    chassis.set_velocity(-velocity, 0, 0)
    time.sleep(inches * duration_per_inch)
    chassis.set_velocity(0, 0, 0)
    print("Completed moving forward.")

def strafe(side='left', distance=6):
    velocity = 50
    duration_per_inch = 0.25
    strafe_velocity = 0.5

    if side == 'left':
        strafe_direction = -strafe_velocity
    elif side == 'right':
        strafe_direction = strafe_velocity
    else:
        raise ValueError("Invalid side for strafing. Use 'left' or 'right'.")

    print(f"Strafing {side} for {distance} inches.")
    chassis.set_velocity(0, 0, strafe_direction)
    time.sleep(distance * duration_per_inch)
    chassis.set_velocity(0, 0, 0)
    print(f"Completed strafing {side}.")

if __name__ == '__main__':
    while start:
        strafe_inches(5)
        break

    print('Closed')