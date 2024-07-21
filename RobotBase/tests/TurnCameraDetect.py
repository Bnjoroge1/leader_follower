#!/usr/bin/python3
# coding=utf8
import sys
sys.path.append('/home/pi/TurboPi/')
import cv2
import time
import signal
import threading
import numpy as np
import yaml_handle
import HiwonderSDK.Board as Board
import HiwonderSDK.mecanum as mecanum
import HiwonderSDK.FourInfrared as infrared
import matplotlib.pyplot as plt
from functionality_classes.ColorSensor import ColorSensor

if sys.version_info.major == 2:
    print('Please run this program with python3!')
    sys.exit(0)

car = mecanum.MecanumChassis()
line = infrared.FourInfrared()
color_sensor = ColorSensor()  # Instantiate your color sensor class
detect_color = 'None'
__isRunning = False

def initMove():
    car.set_velocity(0, 90, 0)
    # Initialize any necessary components or configurations here

def move():
    global __isRunning, detect_color

    while True:
        if __isRunning:
            try:
                # Capture an image from the camera (you need to implement this part)
                img = capture_image_from_camera()  # Placeholder function

                # Perform color detection with your ColorSensor class
                detect_color = color_sensor.detect_color(img)

                if detect_color == 'green':  # Adjusted to detect green color
                    print("Detected green color")
                    car.set_velocity(35, 90, 0)  # Adjust velocity for forward movement
                else:
                    car.set_velocity(35, 90, 0)  # Continue moving forward

            except Exception as e:
                print(f"Error: {e}")

        else:
            car.set_velocity(0, 90, 0)  # Stop the car if __isRunning is False
            time.sleep(0.01)

def capture_image_from_camera():
    # Replace this with your actual camera capture code using OpenCV or another library
    # Example placeholder code
    img = cv2.imread('path_to_your_image.jpg')  # Replace with actual image capture
    return img

def manual_stop(signum, frame):
    global __isRunning
    
    print('Closing...')
    __isRunning = False
    car.set_velocity(0, 90, 0)

if __name__ == '__main__':
    initMove()
    __isRunning = True
    signal.signal(signal.SIGINT, manual_stop)

    move_thread = threading.Thread(target=move)
    move_thread.setDaemon(True)
    move_thread.start()

    while __isRunning:
        try:
            time.sleep(0.1)
        except KeyboardInterrupt:
            break

    car.set_velocity(0, 90, 0)  # Ensure the car stops moving on program exit
