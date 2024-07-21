# tested on 7/15; logic can be improved by detecting blue rather than assuming blue if red and green not detected

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

if sys.version_info.major == 2:
    print('Please run this program with python3!')
    sys.exit(0)

# target_color = ('red', 'green', 'blue')
target_color = ('red', 'yellow', 'blue')

lab_data = None

def load_config():
    global lab_data
    lab_data = yaml_handle.get_yaml_data(yaml_handle.lab_file_path)

range_rgb = {
    'red': (0, 0, 255),
    'blue': (255, 0, 0),
    # 'green': (0, 255, 0), # commenting this out since we will be using green as a turn signal
    'yellow':(255, 255, 0) # need to test performance
}

color_list = []
size = (640, 480)
__isRunning = False
detect_color = 'None'
draw_color = range_rgb["black"]

def reset(): 
    global color_list
    global detect_color
    color_list = []
    detect_color = 'None'

def init():
    print("ColorDetect Init")
    load_config()
    reset()

def start():
    global __isRunning
    reset()
    __isRunning = True
    print("ColorDetect Start")

def stop():
    global __isRunning
    __isRunning = False
    print("ColorDetect Stop")

def exit():
    global __isRunning
    __isRunning = False
    print("ColorDetect Exit")

def getAreaMaxContour(contours):
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

def run(img):
    global __isRunning
    global detect_color, draw_color, color_list
    
    if not __isRunning:
        return img
    
    img_copy = img.copy()
    img_h, img_w = img.shape[:2]
    
    frame_resize = cv2.resize(img_copy, size, interpolation=cv2.INTER_NEAREST)
    frame_gb = cv2.GaussianBlur(frame_resize, (3, 3), 3)
    
    frame_lab = cv2.cvtColor(frame_gb, cv2.COLOR_BGR2LAB)

    color_area_max = None
    max_area = 0
    areaMaxContour_max = 0
    
    for i in target_color:
        if i in lab_data:
            frame_mask = cv2.inRange(frame_lab,
                                     (lab_data[i]['min'][0],
                                      lab_data[i]['min'][1],
                                      lab_data[i]['min'][2]),
                                     (lab_data[i]['max'][0],
                                      lab_data[i]['max'][1],
                                      lab_data[i]['max'][2]))
            opened = cv2.morphologyEx(frame_mask, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
            closed = cv2.morphologyEx(opened, cv2.MORPH_CLOSE, np.ones((3, 3), np.uint8))
            contours = cv2.findContours(closed, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)[-2]
            areaMaxContour, area_max = getAreaMaxContour(contours)
            if areaMaxContour is not None:
                if area_max > max_area:
                    max_area = area_max
                    color_area_max = i
                    areaMaxContour_max = areaMaxContour
    
    if max_area > 2500:
        if color_area_max == 'red':
            detect_color = 'red'
        elif color_area_max == 'yellow':
            detect_color = 'yellow'
        else:
            detect_color = 'blue'
    else:
        detect_color = 'blue'
    
    # print(f"Max area: {max_area}, Detected color area max: {color_area_max}")
    print("Detected color:", detect_color)
    return img

def manual_stop(signum, frame):
    global __isRunning
    
    print('Closing...')
    __isRunning = False

if __name__ == '__main__':
    init()
    start()
    camera = Camera.Camera()
    camera.camera_open(correction=True)
    signal.signal(signal.SIGINT, manual_stop)
    while __isRunning:
        img = camera.frame
        if img is not None:
            frame = img.copy()
            run(frame)  
            key = cv2.waitKey(1)
            if key == 27:
                break
        else:
            time.sleep(0.01)
    camera.camera_close()
    cv2.destroyAllWindows()