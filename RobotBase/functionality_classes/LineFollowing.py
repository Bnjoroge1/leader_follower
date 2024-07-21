#!/usr/bin/python3
# coding=utf8
import sys
import time
import threading
import numpy as np
sys.path.append('/home/pi/TurboPi/')
import yaml_handle
import HiwonderSDK.Board as Board
import HiwonderSDK.mecanum as mecanum
import HiwonderSDK.FourInfrared as infrared
import signal

if sys.version_info.major == 2:
    print('Please run this program with python3!')
    sys.exit(0)

class LineFollowing:
    range_rgb = {
        'red': (0, 0, 255),
        'blue': (255, 0, 0),
        'green': (0, 255, 0),
        'black': (0, 0, 0),
        'white': (255, 255, 255),
    }

    def __init__(self):
        self.car = mecanum.MecanumChassis()
        self.line = infrared.FourInfrared()
        self.servo_data = None
        self.__isRunning = False
        self.car_stop = False
        self.detect_color = 'None'
        self.color_list = []
        self.draw_color = self.range_rgb["black"]
        self.load_config()
        self.initMove()

    def load_config(self):
        self.servo_data = yaml_handle.get_yaml_data(yaml_handle.servo_file_path)

    def initMove(self):
        self.car.set_velocity(0, 90, 0)
        Board.setPWMServoPulse(1, self.servo_data['servo1'], 1000)
        Board.setPWMServoPulse(2, self.servo_data['servo2'], 1000)

    def setBuzzer(self, timer):
        Board.setBuzzer(0)
        Board.setBuzzer(1)
        time.sleep(timer)
        Board.setBuzzer(0)

    def reset(self): 
        self.car_stop = False
        self.detect_color = 'None'
        self.color_list = []
        self.__isRunning = False

    def init(self):
        print("LineFollower Init")
        self.reset()
        self.initMove()

    def start(self):
        self.reset()
        self.__isRunning = True
        self.car.set_velocity(35, 90, 0)
        print("LineFollower Start")

    def stop(self):
        self.car_stop = True
        self.__isRunning = False
        self.set_rgb('None')
        print("LineFollower Stop")

    def exit(self):
        self.car_stop = True
        self.__isRunning = False
        self.set_rgb('None')
        print("LineFollower Exit")

    def setTargetColor(self, color):
        self.target_color = color
        return True, ()

    def set_rgb(self, color):
        if color in self.range_rgb:
            rgb_color = self.range_rgb[color]
            Board.RGB.setPixelColor(0, Board.PixelColor(*rgb_color))
            Board.RGB.setPixelColor(1, Board.PixelColor(*rgb_color))
            Board.RGB.show()
        else:
            Board.RGB.setPixelColor(0, Board.PixelColor(0, 0, 0))
            Board.RGB.setPixelColor(1, Board.PixelColor(0, 0, 0))
            Board.RGB.show()

    def move(self):
        while True:
            if self.__isRunning:
                try:
                    sensor_data = self.line.readData()
                    print(f"Sensor data: {sensor_data}")

                    if sensor_data == [1, 1, 1, 1]:
                        angular_velocity = 0
                    elif sensor_data == [0, 1, 1, 0]:
                        angular_velocity = 0
                    elif sensor_data == [0, 0, 1, 0]:
                        angular_velocity = 0.03
                    elif sensor_data == [0, 1, 0, 0]:
                        angular_velocity = -0.03
                    elif sensor_data == [0, 0, 0, 1]:
                        angular_velocity = 0.3
                    elif sensor_data == [1, 0, 0, 0]:
                        angular_velocity = -0.3
                    else:
                        angular_velocity = 0

                    self.car.set_velocity(35, 90, angular_velocity)

                    if self.detect_color == 'green':
                        print("Detected green color")
                        self.car.set_velocity(35, 90, 0)

                except OSError as e:
                    print(f"I/O Error: {e}")
            else:
                print("Stopping movement")
                self.car.set_velocity(0, 90, 0)
                time.sleep(0.01)

    def run(self, img):
        if not self.__isRunning:
            return img

        self.detect_color = 'None'
        self.draw_color = self.range_rgb["black"]
        cv2.putText(img, "Color: " + self.detect_color, (10, img.shape[0] - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.65, self.draw_color, 2)
        return img

    def manualcar_stop(self, signum, frame):
        print('Manual Stop')
        self.__isRunning = False
        self.car.set_velocity(0, 90, 0)

if __name__ == '__main__':
    line_follower = LineFollowing()
    line_follower.init()
    line_follower.start()
    signal.signal(signal.SIGINT, line_follower.manualcar_stop)
    move_thread = threading.Thread(target=line_follower.move)
    move_thread.setDaemon(True)
    move_thread.start()

    while line_follower.__isRunning:
        time.sleep(0.01)
