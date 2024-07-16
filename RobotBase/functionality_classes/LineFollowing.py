#!/usr/bin/python3
# coding=utf8
import sys
sys.path.append('/home/pi/TurboPi/')
import time
import math
import signal
import threading
import numpy as np
import yaml_handle
import HiwonderSDK.Board as Board
import HiwonderSDK.mecanum as mecanum
import HiwonderSDK.FourInfrared as infrared
import matplotlib.pyplot as plt

if sys.version_info.major == 2:
    print('Please run this program with python3!')
    sys.exit(0)

car = mecanum.MecanumChassis()
line = infrared.FourInfrared()

servo_data = None
__isRunning = False  # Ensure __isRunning is defined globally
car_stop = False     # Initialize car_stop globally

def load_config():
    global servo_data
    servo_data = yaml_handle.get_yaml_data(yaml_handle.servo_file_path)

def initMove():
    car.set_velocity(0, 90, 0)
    Board.setPWMServoPulse(1, servo_data['servo1'], 1000)
    Board.setPWMServoPulse(2, servo_data['servo2'], 1000)

def setBuzzer(timer):
    Board.setBuzzer(0)
    Board.setBuzzer(1)
    time.sleep(timer)
    Board.setBuzzer(0)

range_rgb = {
    'red': (0, 0, 255),
    'blue': (255, 0, 0),
    'green': (0, 255, 0),
    'black': (0, 0, 0),
    'white': (255, 255, 255),
}

draw_color = range_rgb["black"]

def reset(): 
    global car_stop, detect_color, color_list, __isRunning
    car_stop = False
    detect_color = 'None'
    color_list = []
    __isRunning = False

def init():
    print("LineFollower Init")
    load_config()
    reset()
    initMove()

def start():
    global __isRunning
    reset()
    __isRunning = True
    car.set_velocity(35, 90, 0)
    print("LineFollower Start")

def stop():
    global car_stop, __isRunning
    car_stop = True
    __isRunning = False
    set_rgb('None')
    print("LineFollower Stop")

def exit():
    global car_stop, __isRunning
    car_stop = True
    __isRunning = False
    set_rgb('None')
    print("LineFollower Exit")

def setTargetColor(color):
    global target_color
    target_color = color
    return True, ()

def set_rgb(color):
    if color in range_rgb:
        rgb_color = range_rgb[color]
        Board.RGB.setPixelColor(0, Board.PixelColor(*rgb_color))
        Board.RGB.setPixelColor(1, Board.PixelColor(*rgb_color))
        Board.RGB.show()
    else:
        Board.RGB.setPixelColor(0, Board.PixelColor(0, 0, 0))
        Board.RGB.setPixelColor(1, Board.PixelColor(0, 0, 0))
        Board.RGB.show()

def move():
    global car_stop, __isRunning, detect_color

    while True:
        if __isRunning:
            try:
                sensor_data = line.readData()
                print(f"Sensor data: {sensor_data}")  # Debug print for sensor data

                # Calculate angular velocity based on sensor data
                if sensor_data == [1, 1, 1, 1]:
                    angular_velocity = 0  # All sensors detect the line, go straight
                elif sensor_data == [0, 1, 1, 0]:
                    angular_velocity = 0  # Sensors 2 and 3 detect the line, go straight
                elif sensor_data == [0, 0, 1, 0]:
                    angular_velocity = 0.03  # Sensor 3 detects the line, turn slightly right
                elif sensor_data == [0, 1, 0, 0]:
                    angular_velocity = -0.03  # Sensor 2 detects the line, turn slightly left
                elif sensor_data == [0, 0, 0, 1]:
                    angular_velocity = 0.3  # Sensor 4 detects the line, turn right
                elif sensor_data == [1, 0, 0, 0]:
                    angular_velocity = -0.3  # Sensor 1 detects the line, turn left
                else:
                    angular_velocity = 0  # No sensors detect the line, stop

                car.set_velocity(35, 90, angular_velocity)

                if detect_color == 'green':
                    print("Detected green color")
                    car.set_velocity(35, 90, 0)

            except OSError as e:
                print(f"I/O Error: {e}")
        else:
            print("Stopping movement")
            car.set_velocity(0, 90, 0)
            time.sleep(0.01)

th = threading.Thread(target=move)
th.setDaemon(True)
th.start()

def run(img):
    global __isRunning, detect_color, draw_color, color_list

    if not __isRunning:
        return img

    detect_color = 'None'
    draw_color = range_rgb["black"]
    cv2.putText(img, "Color: " + detect_color, (10, img.shape[0] - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.65, draw_color, 2)
    return img

def manualcar_stop(signum, frame):
    global __isRunning
    print('Manual Stop')
    __isRunning = False
    car.set_velocity(0, 90, 0)

if __name__ == '__main__':
    init()
    start()
    signal.signal(signal.SIGINT, manualcar_stop)
    while __isRunning:
        time.sleep(0.01)
