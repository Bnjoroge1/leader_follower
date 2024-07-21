#!/usr/bin/python3
# coding=utf8
import sys
sys.path.append('/home/pi/TurboPi/')
import cv2
import time
import math
import signal
import Camera
import threading
import numpy as np
import yaml_handle
import HiwonderSDK.Board as Board
import HiwonderSDK.mecanum as mecanum

if sys.version_info.major == 2:
    print('Please run this program with python3!')
    sys.exit(0)

class ColorSensor:
    target_color = ('red', 'green', 'blue')
    
    def __init__(self):
        self.lab_data = None
        self.range_rgb = {
            'red': (0, 0, 255),
            'blue': (255, 0, 0),
            'green': (0, 255, 0),
            # 'yellow': (255, 255, 0),
            'black': (0, 0, 0),
        }
        self.color_list = []
        self.size = (640, 480)
        self.is_running = False
        self.detect_color = 'None'
        self.draw_color = self.range_rgb["black"]
        self.camera = Camera.Camera()
        self.car = mecanum.MecanumChassis()

    def load_config(self):
        self.lab_data = yaml_handle.get_yaml_data(yaml_handle.lab_file_path)

    def reset(self): 
        self.color_list = []
        self.detect_color = 'None'

    def init(self):
        print("ColorDetect Init")
        self.load_config()
        self.reset()

    def start(self):
        self.reset()
        self.is_running = True
        print("ColorDetect Start")
        self.camera.camera_open(correction=True)

    def stop(self):
        self.is_running = False
        print("ColorDetect Stop")
        self.camera.camera_close()

    def exit(self):
        self.is_running = False
        print("ColorDetect Exit")
        self.camera.camera_close()

    def get_area_max_contour(self, contours):
        contour_area_temp = 0
        contour_area_max = 0
        area_max_contour = None

        for c in contours:
            contour_area_temp = math.fabs(cv2.contourArea(c))
            if contour_area_temp > contour_area_max:
                contour_area_max = contour_area_temp
                if contour_area_temp > 300:
                    area_max_contour = c

        return area_max_contour, contour_area_max

    def run(self, img):
        if not self.is_running:
            return img
        
        img_copy = img.copy()
        img_h, img_w = img.shape[:2]
        
        frame_resize = cv2.resize(img_copy, self.size, interpolation=cv2.INTER_NEAREST)
        frame_gb = cv2.GaussianBlur(frame_resize, (3, 3), 3)
        
        frame_lab = cv2.cvtColor(frame_gb, cv2.COLOR_BGR2LAB)

        color_area_max = None
        max_area = 0
        area_max_contour_max = 0
        
        for i in self.target_color:
            if i in self.lab_data:
                frame_mask = cv2.inRange(frame_lab,
                                        (self.lab_data[i]['min'][0],
                                        self.lab_data[i]['min'][1],
                                        self.lab_data[i]['min'][2]),
                                        (self.lab_data[i]['max'][0],
                                        self.lab_data[i]['max'][1],
                                        self.lab_data[i]['max'][2]))
                opened = cv2.morphologyEx(frame_mask, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
                closed = cv2.morphologyEx(opened, cv2.MORPH_CLOSE, np.ones((3, 3), np.uint8))
                contours = cv2.findContours(closed, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)[-2]
                area_max_contour, area_max = self.get_area_max_contour(contours)
                if area_max_contour is not None:
                    if area_max > max_area:
                        max_area = area_max
                        color_area_max = i
                        area_max_contour_max = area_max_contour
        
        if max_area > 2500:
            if color_area_max == 'red':
                self.detect_color = 'red'
            elif color_area_max == 'green':
                self.detect_color = 'green'
            elif color_area_max == 'blue':
                self.detect_color = 'blue'
        else:
            self.detect_color = 'None'
        
        print("Detected color:", self.detect_color)
        self.move_based_on_color()
        return img

    def get_detected_color(self):
        return self.detect_color

    def move_based_on_color(self):
        if self.detect_color == 'green':
            print("Detected green color, turning left")
            self.car.set_velocity(35, 45, 0)  # Turn left
        else:
            self.car.set_velocity(35, 90, 0)  # Move forward

    def manual_stop(self, signum, frame):
        self.car.set_velocity(0, 0, 0)  # Stop the car when exiting
        self.is_running = False
        print('Closing...')
        self.camera.camera_close()

if __name__ == '__main__':
    color_sensor = ColorSensor()
    color_sensor.init()
    color_sensor.start()
    signal.signal(signal.SIGINT, color_sensor.manual_stop)
    while color_sensor.is_running:
        img = color_sensor.camera.frame
        if img is not None:
            frame = img.copy()
            color_sensor.run(frame)  
            key = cv2.waitKey(1)
            if key == 27:
                break
        else:
            time.sleep(0.01)
    color_sensor.camera.camera_close()
    cv2.destroyAllWindows()
