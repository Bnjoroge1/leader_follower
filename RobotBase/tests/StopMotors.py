#!/usr/bin/python3
# coding=utf8
import os
import sys
import time
import signal
import threading

current_dir = os.path.dirname(os.path.realpath(__file__))
parent_dir = os.path.abspath(os.path.join(current_dir, os.pardir))
sys.path.append(parent_dir)
sys.path.append('/home/pi/TurboPi/')

import HiwonderSDK.mecanum as mecanum

sys.path.append(os.path.join(current_dir, 'functionality_classes'))

if sys.version_info.major == 2:
    print('Please run this program with python3!')
    sys.exit(0)

car = mecanum.MecanumChassis()
__isRunning = False

def initMove():
    car.set_velocity(0, 0, 0)
    print("Initialization complete. Car set to stop.")

def manual_stop(signum, frame):
    global __isRunning
    __isRunning = False
    car.set_velocity(0, 0, 0)

if __name__ == '__main__':
    initMove()
    __isRunning = True