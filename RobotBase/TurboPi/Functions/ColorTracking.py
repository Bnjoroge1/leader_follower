#!/usr/bin/python3
# coding=utf8
import sys
sys.path.append('/home/pi/TurboPi/')
import cv2
import time
import math
import signal
import Camera
import argparse
import threading
import numpy as np
import yaml_handle
import HiwonderSDK.PID as PID
import HiwonderSDK.Misc as Misc
import HiwonderSDK.Board as Board
import HiwonderSDK.mecanum as mecanum

# Color tracking

if sys.version_info.major == 2:
    print('Please run this program with python3!')
    sys.exit(0)
    
car = mecanum.MecanumChassis()

servo1 = 1500
servo2 = 1500
servo_x = servo2
servo_y = servo1

color_radius = 0
color_center_x = -1
color_center_y = -1

car_en = False
wheel_en = False
size = (640, 480)
target_color = ()
__isRunning = False

car_x_pid = PID.PID(P=0.15, I=0.001, D=0.0001) # Pid Initialization
car_y_pid = PID.PID(P=1.00, I=0.001, D=0.0001)
servo_x_pid = PID.PID(P=0.06, I=0.0003, D=0.0006)  
servo_y_pid = PID.PID(P=0.06, I=0.0003, D=0.0006)

lab_data = None
servo_data = None
def load_config():
    global lab_data, servo_data
    
    lab_data = yaml_handle.get_yaml_data(yaml_handle.lab_file_path)
    servo_data = yaml_handle.get_yaml_data(yaml_handle.servo_file_path)


# Initial Position 
def initMove():
    Board.setPWMServoPulse(1, servo1, 1000)
    Board.setPWMServoPulse(2, servo2, 1000)

range_rgb = {
    'red': (0, 0, 255),
    'blue': (255, 0, 0),
    'green': (0, 255, 0),
    'black': (0, 0, 0),
    'white': (255, 255, 255),
}

# Set Buzzer
def setBuzzer(timer):
    Board.setBuzzer(0)
    Board.setBuzzer(1)
    time.sleep(timer)
    Board.setBuzzer(0)

# Turn off motor
def car_stop():
    car.set_velocity(0,90,0)  # Turn off all motors


#The color of RGB light on expansion board is set to consistent with the tracked color 
def set_rgb(color):
    if color == "red":
        Board.RGB.setPixelColor(0, Board.PixelColor(255, 0, 0))
        Board.RGB.setPixelColor(1, Board.PixelColor(255, 0, 0))
        Board.RGB.show()
    elif color == "green":
        Board.RGB.setPixelColor(0, Board.PixelColor(0, 255, 0))
        Board.RGB.setPixelColor(1, Board.PixelColor(0, 255, 0))
        Board.RGB.show()
    elif color == "blue":
        Board.RGB.setPixelColor(0, Board.PixelColor(0, 0, 255))
        Board.RGB.setPixelColor(1, Board.PixelColor(0, 0, 255))
        Board.RGB.show()
    else:
        Board.RGB.setPixelColor(0, Board.PixelColor(0, 0, 0))
        Board.RGB.setPixelColor(1, Board.PixelColor(0, 0, 0))
        Board.RGB.show()


# Reset Variables
def reset():
    global target_color, car_en
    global servo1, servo2, wheel_en
    global servo_x, servo_y, color_radius
    global color_center_x, color_center_y
    
    car_en = False
    wheel_en = False
    servo1 = servo_data['servo1']
    servo2 = servo_data['servo2']
    servo_x = servo2
    servo_y = servo1
    target_color = ()
    car_x_pid.clear()
    car_y_pid.clear()
    servo_x_pid.clear()
    servo_y_pid.clear()
    color_radius = 0
    color_center_x = -1
    color_center_y = -1
    

# APP Initialization
def init():
    print("ColorTracking Init")
    load_config()
    reset()
    initMove()

# App starts calling game program
def start():
    global __isRunning
    reset()
    __isRunning = True
    print("ColorTracking Start")

# App stops calling game program  
def stop():
    global __isRunning
    reset()
    initMove()
    car_stop()
    __isRunning = False
    set_rgb('None')
    print("ColorTracking Stop")

# Exit the game
def exit():
    global __isRunning
    reset()
    initMove()
    car_stop()
    __isRunning = False
    set_rgb('None')
    print("ColorTracking Exit")

# Set the target color
def setTargetColor(color):
    global target_color

    print("COLOR", color)
    target_color = color
    return (True, ())

# Set car following
def setVehicleFollowing(state):
    global wheel_en
    
    print("wheel_en", state)
    wheel_en = state
    if not wheel_en:
        car_stop()
    return (True, ())

# Find the maximum contour 
# Parameters are the list of contours to be compared 
def getAreaMaxContour(contours):
    contour_area_temp = 0
    contour_area_max = 0
    areaMaxContour = None
    for c in contours:  # Loop over the contours
        contour_area_temp = math.fabs(cv2.contourArea(c))  # Calculate the contour area 
        if contour_area_temp > contour_area_max:
            contour_area_max = contour_area_temp
            if contour_area_temp > 300:  # Only when the area is greater than 300, the maximum contour takes effect to filter the interference
                areaMaxContour = c
    return areaMaxContour, contour_area_max  # Return the maximum contour

# Movement Processing
def move():
    global __isRunning, car_en, wheel_en
    global servo_x, servo_y, color_radius
    global color_center_x, color_center_y
    
    img_w, img_h = size[0], size[1]
    
    while True:
        if __isRunning:
            if color_center_x != -1 and color_center_y != -1:
                # Camera pan-tilt tracking
                # Track based on the camera x-axis coordiate
                if abs(color_center_x - img_w/2.0) < 15: # The movement is quite small, so do not need to move
                    color_center_x = img_w/2.0
                servo_x_pid.SetPoint = img_w/2.0    # Set 
                servo_x_pid.update(color_center_x)  # Current
                servo_x += int(servo_x_pid.output)  # Access PID output
                
                servo_x = 800 if servo_x < 800 else servo_x  # Set servo range
                servo_x = 2200 if servo_x > 2200 else servo_x
                
                # Track based on the y-axis coordinate 
                if abs(color_center_y - img_h/2.0) < 10: # The movement is quite small, so do not need to move
                    color_center_y = img_h/2.0
                servo_y_pid.SetPoint = img_h/2.0   # Set 
                servo_y_pid.update(color_center_y) # Get the current centre position
                servo_y -= int(servo_y_pid.output) # Access PID output
                
                servo_y = 1200 if servo_y < 1200 else servo_y # Set servo range
                servo_y = 1900 if servo_y > 1900 else servo_y
                
                Board.setPWMServoPulse(1, servo_y, 20) # Set servo pulse
                Board.setPWMServoPulse(2, servo_x, 20)
                time.sleep(0.01)
                
                # Car following
                if wheel_en:
                    # Track according the target distance
                    if abs(color_radius - 100) < 10: 
                        car_y_pid.SetPoint = color_radius
                    else:
                        car_y_pid.SetPoint = 100
                    car_y_pid.update(color_radius)
                    dy = car_y_pid.output   # Access PID output value
                    dy = 0 if abs(dy) < 15 else dy # set the speed range
                    
                    # Track according to the x-axis value of the servo 
                    if abs(servo_x - servo2) < 15:
                        car_x_pid.SetPoint = servo_x
                    else:
                        car_x_pid.SetPoint = servo2
                    car_x_pid.update(servo_x)
                    dx = car_x_pid.output   # Access PID output value
                    dx = 0 if abs(dx) < 15 else dx # Set the speed range
                    
                    car.translation(dx, dy) # Robot is set to move (a-axis speed, y-axis speed)
                    car_en = True
                
                time.sleep(0.01)
                
            else:
                if car_en:
                    car_stop()
                    car_en = False
        else:
            if car_en:
                car_stop()
                car_en = False
            time.sleep(0.01)

# Run child thread 
th = threading.Thread(target=move)
th.setDaemon(True)
th.start()

# Image processing
def run(img):
    global __isRunning, color_radius
    global color_center_x, color_center_y
    
    img_copy = img.copy()
    img_h, img_w = img.shape[:2]
    
    if not __isRunning:   # Detect whether the game is started, if not, the orginal image will be returned
        return img
     
    frame_resize = cv2.resize(img_copy, size, interpolation=cv2.INTER_NEAREST)
    frame_gb = cv2.GaussianBlur(frame_resize, (3, 3), 3)   
    frame_lab = cv2.cvtColor(frame_gb, cv2.COLOR_BGR2LAB)  # Convert image into LAB space
    
    area_max = 0
    areaMaxContour = 0
    for i in target_color:
        if i in lab_data:
            frame_mask = cv2.inRange(frame_lab,
                                         (lab_data[i]['min'][0],
                                          lab_data[i]['min'][1],
                                          lab_data[i]['min'][2]),
                                         (lab_data[i]['max'][0],
                                          lab_data[i]['max'][1],
                                          lab_data[i]['max'][2]))  #Bitwise operation of the original 
            opened = cv2.morphologyEx(frame_mask, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))  # Opening 
            closed = cv2.morphologyEx(opened, cv2.MORPH_CLOSE, np.ones((3, 3), np.uint8))  # Closing
            contours = cv2.findContours(closed, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)[-2]  # Find contour
            areaMaxContour, area_max = getAreaMaxContour(contours)  # Find the maximum contour
    if area_max > 1000:  # Find the maximum contour
        (center_x, center_y), radius = cv2.minEnclosingCircle(areaMaxContour)  # Obtain the minimum circumcircle of an object
        color_radius = int(Misc.map(radius, 0, size[0], 0, img_w))
        color_center_x = int(Misc.map(center_x, 0, size[0], 0, img_w))
        color_center_y = int(Misc.map(center_y, 0, size[1], 0, img_h))
        if color_radius > 300:
            color_radius = 0
            color_center_x = -1
            color_center_y = -1
            return img
        
        cv2.circle(img, (color_center_x, color_center_y), color_radius, range_rgb[i], 2)
        
    else:
        color_radius = 0
        color_center_x = -1
        color_center_y = -1
            
    return img


#Processing before exit
def manual_stop(signum, frame):
    global __isRunning
    
    print('Closing...')
    __isRunning = False
    car_stop()  # Turn off all motors 
    initMove()  # Motor returns to the initial position

if __name__ == '__main__':
    init()
    start()
    target_color = ('red',)
	whell_en = True
    camera = Camera.Camera()
    camera.camera_open(correction=True) # Enable distortion correction which is not enabled by default
    signal.signal(signal.SIGINT, manual_stop)
    while __isRunning:
        img = camera.frame
        if img is not None:
            frame = img.copy()
            Frame = run(frame)  
            frame_resize = cv2.resize(Frame, (320, 240)) # Resize the frame to 230*240
            cv2.imshow('frame', frame_resize)
            key = cv2.waitKey(1)
            if key == 27:
                break
        else:
            time.sleep(0.01)
    camera.camera_close()
    cv2.destroyAllWindows()
