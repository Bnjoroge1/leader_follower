#!/usr/bin/python3
# coding=utf8

import sys
sys.path.append('/home/pi/TurboPi/')
import time
import signal
import os
import HiwonderSDK.mecanum as mecanum

current_dir = os.path.dirname(os.path.realpath(__file__))
parent_dir = os.path.abspath(os.path.join(current_dir, os.pardir))
sys.path.append(parent_dir)
sys.path.append(os.path.join(current_dir, 'functionality_classes'))

from functionality_classes.UltrasonicSensor import Sonar

if sys.version_info.major == 2:
    print('Please run this program with python3!')
    sys.exit(0)

chassis = mecanum.MecanumChassis()
sonar = Sonar()

start = True

desired_distance = 300
tolerance = 2

def Stop(signum, frame):
    global start
    start = False
    print('Closing...')
    chassis.set_velocity(0, 0, 0)

signal.signal(signal.SIGINT, Stop)

def get_distance():
    distances = [sonar.getDistance() / 10 for _ in range(5)]
    avg_distance = sum(distances) / len(distances)
    print(f"Smoothed distance from the wall: {avg_distance:.1f} cm")
    return avg_distance

def move_to_distance():
    move_velocity = 50
    while start:
        distance = get_distance()
        if distance < (desired_distance - tolerance):
            chassis.set_velocity(-move_velocity, 0, 0)
            print("Moving backward to increase distance.")
        elif distance > (desired_distance + tolerance):
            chassis.set_velocity(move_velocity, 0, 0)
            print("Moving forward to decrease distance.")
        else:
            chassis.set_velocity(0, 0, 0)
            print("Within the desired range. Starting to strafe right.")
            strafe_right()
            break
        time.sleep(0.5)

def strafe_right():
    strafe_velocity = 50
    while start:
        distance = get_distance()
        if distance < (desired_distance - tolerance):
            chassis.set_velocity(0, strafe_velocity, 0)
            print("Strafing right to correct position.")
        elif distance > (desired_distance + tolerance):
            chassis.set_velocity(0, -strafe_velocity, 0)
            print("Strafing left to correct position.")
        else:
            chassis.set_velocity(0, 0, 0)
            print("Maintaining position.")
        time.sleep(0.5)

if __name__ == '__main__':
    try:
        print("Moving to the desired distance from the wall.")
        move_to_distance()
    except KeyboardInterrupt:
        pass

    print('Closed')