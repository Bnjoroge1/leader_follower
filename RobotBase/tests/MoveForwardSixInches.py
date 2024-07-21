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

def move_forward_inches(inches):
    velocity = 50
    duration_per_inch = 0.5
    print(f"Moving forward {inches} inches.")
    chassis.set_velocity(velocity, 90, 0)
    time.sleep(inches * duration_per_inch)
    chassis.set_velocity(0, 0, 0)
    print("Completed moving forward.")

if __name__ == '__main__':
    while start:
        move_forward_inches(6)
        break

    print('Closed')
